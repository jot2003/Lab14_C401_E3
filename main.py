import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple

from engine.runner import BenchmarkRunner
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from agent.main_agent import MainAgent

import re

# ---------------------------------------------------------------------------
# RAGAS-style evaluator — computes real token-overlap metrics
# ---------------------------------------------------------------------------
class ExpertEvaluator:
    def __init__(self):
        self.retrieval_eval = RetrievalEvaluator()

    @staticmethod
    def _tokenize(text: str):
        return set(re.findall(r"\w+", (text or "").lower()))

    def calculate_hit_rate(self, expected_ids, retrieved_ids, top_k=3):
        return self.retrieval_eval.calculate_hit_rate(expected_ids, retrieved_ids, top_k)

    def calculate_mrr(self, expected_ids, retrieved_ids):
        return self.retrieval_eval.calculate_mrr(expected_ids, retrieved_ids)

    async def score(self, case, resp):
        answer = resp.get("answer", "") if isinstance(resp, dict) else str(resp)
        context_text = case.get("context", "")
        expected = case.get("expected_answer", "")
        question = case.get("question", "")

        a_tok = self._tokenize(answer)
        c_tok = self._tokenize(context_text)
        e_tok = self._tokenize(expected)
        q_tok = self._tokenize(question)

        # Faithfulness: how much of the answer is grounded in context
        faithfulness = len(a_tok & c_tok) / max(1, len(a_tok))
        # Relevancy: how much of the answer relates to the question
        relevancy = len(a_tok & q_tok) / max(1, len(q_tok))
        # Correctness: overlap with expected answer
        correctness = len(a_tok & e_tok) / max(1, len(e_tok))

        # Get retrieval IDs for real hit_rate/mrr
        expected_ids = []
        if isinstance(case.get("metadata"), dict):
            expected_ids = case["metadata"].get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("retrieved_ids") or []
        if not retrieved_ids and isinstance(resp.get("metadata"), dict):
            retrieved_ids = resp["metadata"].get("sources", [])

        hit_rate = self.retrieval_eval.calculate_hit_rate(expected_ids, retrieved_ids) if expected_ids else 1.0
        mrr = self.retrieval_eval.calculate_mrr(expected_ids, retrieved_ids) if expected_ids else 1.0

        return {
            "faithfulness": round(faithfulness, 4),
            "relevancy": round(relevancy, 4),
            "correctness": round(correctness, 4),
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr},
        }


# ---------------------------------------------------------------------------
# Cost Tracker — estimates API spend per benchmark run
# ---------------------------------------------------------------------------
PRICE_PER_1K_TOKENS = {
    "gpt-4o":      {"input": 0.0025, "output": 0.010},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}
AVG_INPUT_TOKENS_PER_CALL  = 220   # prompt + question + answer + ground truth
AVG_OUTPUT_TOKENS_PER_CALL = 80    # JSON score response


@dataclass
class CostReport:
    total_cases: int = 0
    judge_calls: int = 0
    estimated_usd: float = 0.0
    cost_per_case_usd: float = 0.0
    judge_breakdown: Dict[str, float] = field(default_factory=dict)
    mode: str = "heuristic_local"

    def to_dict(self) -> Dict:
        return asdict(self)


def estimate_cost(judge_models: List[str], total_cases: int, live_mode: bool) -> CostReport:
    if not live_mode:
        return CostReport(
            total_cases=total_cases,
            judge_calls=0,
            estimated_usd=0.0,
            cost_per_case_usd=0.0,
            judge_breakdown={m: 0.0 for m in judge_models},
            mode="heuristic_local (no API cost)",
        )

    breakdown: Dict[str, float] = {}
    total_usd = 0.0
    total_calls = total_cases * len(judge_models)

    for model in judge_models:
        prices = PRICE_PER_1K_TOKENS.get(model, {"input": 0.003, "output": 0.012})
        cost = total_cases * (
            AVG_INPUT_TOKENS_PER_CALL  / 1000 * prices["input"]
            + AVG_OUTPUT_TOKENS_PER_CALL / 1000 * prices["output"]
        )
        breakdown[model] = round(cost, 6)
        total_usd += cost

    return CostReport(
        total_cases=total_cases,
        judge_calls=total_calls,
        estimated_usd=round(total_usd, 6),
        cost_per_case_usd=round(total_usd / max(1, total_cases), 6),
        judge_breakdown=breakdown,
        mode="openai_api_live",
    )


# ---------------------------------------------------------------------------
# Regression Gate — multi-threshold release decision
# ---------------------------------------------------------------------------
@dataclass
class GateThresholds:
    min_avg_score:       float = 3.0    # absolute quality floor (out of 5)
    min_hit_rate:        float = 0.8    # retrieval must be reliable
    min_agreement_rate:  float = 0.7    # judges must agree sufficiently
    max_manual_review:   float = 0.10   # at most 10 % flagged for review
    min_score_delta:     float = -0.05  # allow up to 5 % regression vs baseline


@dataclass
class GateResult:
    decision: str               # "RELEASE" | "ROLLBACK"
    passed: bool
    reasons: List[str]
    failed_checks: List[str]
    metrics_snapshot: Dict[str, Any]
    thresholds: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


def run_regression_gate(
    v1_summary: Dict,
    v2_summary: Dict,
    thresholds: Optional[GateThresholds] = None,
) -> GateResult:
    t = thresholds or GateThresholds()
    v2m = v2_summary["metrics"]
    v1m = v1_summary["metrics"]

    avg_score      = v2m["avg_score"]
    hit_rate       = v2m["hit_rate"]
    agreement_rate = v2m["agreement_rate"]
    manual_rate    = v2m.get("manual_review_rate", 0.0)
    delta          = avg_score - v1m["avg_score"]

    checks: List[Tuple[str, bool, str]] = [
        (
            "quality_score",
            avg_score >= t.min_avg_score,
            f"avg_score={avg_score:.3f} (need >= {t.min_avg_score})",
        ),
        (
            "hit_rate",
            hit_rate >= t.min_hit_rate,
            f"hit_rate={hit_rate:.3f} (need >= {t.min_hit_rate})",
        ),
        (
            "judge_agreement",
            agreement_rate >= t.min_agreement_rate,
            f"agreement_rate={agreement_rate:.3f} (need >= {t.min_agreement_rate})",
        ),
        (
            "manual_review_rate",
            manual_rate <= t.max_manual_review,
            f"manual_review_rate={manual_rate:.3f} (need <= {t.max_manual_review})",
        ),
        (
            "regression_delta",
            delta >= t.min_score_delta,
            f"delta={delta:+.3f} (need >= {t.min_score_delta})",
        ),
    ]

    passed_list  = [desc for _, ok, desc in checks if ok]
    failed_list  = [desc for _, ok, desc in checks if not ok]
    all_passed   = len(failed_list) == 0

    return GateResult(
        decision="RELEASE" if all_passed else "ROLLBACK",
        passed=all_passed,
        reasons=passed_list,
        failed_checks=failed_list,
        metrics_snapshot={
            "v1_avg_score":      round(v1m["avg_score"], 4),
            "v2_avg_score":      round(avg_score, 4),
            "delta":             round(delta, 4),
            "hit_rate":          round(hit_rate, 4),
            "agreement_rate":    round(agreement_rate, 4),
            "manual_review_rate": round(manual_rate, 4),
        },
        thresholds=asdict(t),
    )


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------
def calculate_judge_model_averages(results: List[Dict]) -> Dict[str, float]:
    score_map: Dict[str, List[float]] = {}
    for item in results:
        for judge_name, score in item["judge"].get("individual_scores", {}).items():
            score_map.setdefault(judge_name, []).append(score)
    return {
        name: round(sum(vals) / len(vals), 4)
        for name, vals in score_map.items()
        if vals
    }


async def run_benchmark_with_results(
    agent_version: str,
) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
    print(f"  🚀 Khởi động Benchmark: {agent_version} ...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("  ❌ Thiếu data/golden_set.jsonl — chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("  ❌ File data/golden_set.jsonl rỗng.")
        return None, None

    if agent_version == "Agent_V1_Base":
        judge_models = ["gpt-4o-mini"]
        live = True
    else:
        judge_models = ["gpt-4o", "gpt-4o-mini"]
        live = True

    judge  = LLMJudge(judge_models=judge_models, use_live_judges=live)
    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), judge)

    t0      = time.perf_counter()
    results = await runner.run_all(dataset)
    elapsed = time.perf_counter() - t0

    total               = len(results)
    manual_review_count = sum(1 for r in results if r["judge"].get("requires_manual_review"))
    judge_averages      = calculate_judge_model_averages(results)
    cost_report         = estimate_cost(judge_models, total, live)

    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail_count = sum(1 for r in results if r["status"] == "fail")

    summary = {
        "metadata": {
            "version":    agent_version,
            "total":      total,
            "timestamp":  time.strftime("%Y-%m-%d %H:%M:%S"),
            "judge_models": list(judge_averages.keys()),
            "judge_mode": "single-offline" if agent_version == "Agent_V1_Base" else "multi-live-or-fallback",
            "elapsed_sec": round(elapsed, 2),
        },
        "metrics": {
            "avg_score":           round(sum(r["judge"]["final_score"] for r in results) / total, 4),
            "hit_rate":            round(sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total, 4),
            "agreement_rate":      round(sum(r["judge"]["agreement_rate"] for r in results) / total, 4),
            "manual_review_rate":  round(manual_review_count / total, 4),
            "pass_count":          pass_count,
            "fail_count":          fail_count,
            "pass_rate":           round(pass_count / total, 4),
            "judge_model_avg_scores": judge_averages,
        },
        "cost": cost_report.to_dict(),
    }
    return results, summary


async def run_benchmark(version: str) -> Optional[Dict]:
    _, summary = await run_benchmark_with_results(version)
    return summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    print("\n" + "=" * 60)
    print("  AI EVALUATION FACTORY — Regression Gate (D14-T04)")
    print("  Owner: Nguyen Thanh Nam (2A202600205)")
    print("=" * 60 + "\n")

    print("[1/4] Chạy benchmark V1 (baseline) ...")
    v1_summary = await run_benchmark("Agent_V1_Base")

    print("[2/4] Chạy benchmark V2 (optimized) ...")
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")

    if not v1_summary or not v2_summary:
        print("\n❌ Không thể chạy benchmark — kiểm tra lại data/golden_set.jsonl.")
        return

    # ------------------------------------------------------------------
    # Regression Gate decision
    # ------------------------------------------------------------------
    print("\n[3/4] Chạy Regression Gate ...")
    gate_result = run_regression_gate(v1_summary, v2_summary)

    print("\n" + "─" * 60)
    print("  📊 KẾT QUẢ SO SÁNH (REGRESSION)")
    print("─" * 60)
    snap = gate_result.metrics_snapshot
    print(f"  V1 avg_score : {snap['v1_avg_score']}")
    print(f"  V2 avg_score : {snap['v2_avg_score']}")
    print(f"  Delta        : {snap['delta']:+.4f}")
    print(f"  Hit Rate     : {snap['hit_rate']}")
    print(f"  Agreement    : {snap['agreement_rate']}")
    print(f"  Manual Rev.  : {snap['manual_review_rate']}")

    print("\n  ✅ Checks PASSED:")
    for r in gate_result.reasons:
        print(f"     • {r}")

    if gate_result.failed_checks:
        print("\n  ❌ Checks FAILED:")
        for r in gate_result.failed_checks:
            print(f"     • {r}")

    verdict_icon = "✅" if gate_result.passed else "❌"
    print(f"\n{'─' * 60}")
    print(f"  {verdict_icon}  QUYẾT ĐỊNH: {gate_result.decision}")
    print(f"{'─' * 60}\n")

    # ------------------------------------------------------------------
    # Persist reports
    # ------------------------------------------------------------------
    print("[4/4] Lưu reports ...")
    os.makedirs("reports", exist_ok=True)

    # Enrich summary with full regression context
    v2_summary["regression"] = {
        "v1_version":   v1_summary["metadata"]["version"],
        "v2_version":   v2_summary["metadata"]["version"],
        "gate_decision": gate_result.decision,
        "gate_passed":   gate_result.passed,
        "gate_details":  gate_result.to_dict(),
        "v1_metrics":    v1_summary["metrics"],
    }

    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    print("  ✔ reports/summary.json")

    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)
    print("  ✔ reports/benchmark_results.json")

    # Cost summary
    cost = v2_summary["cost"]
    print(f"\n  💰 Chi phí ước tính V2: ${cost['estimated_usd']:.4f} "
          f"(${cost['cost_per_case_usd']:.6f}/case) — mode: {cost['mode']}")
    if cost["estimated_usd"] == 0:
        print("  💡 Tip giảm chi phí: Đang chạy heuristic local (miễn phí).")
        print("     Khi dùng API live, dùng gpt-4o-mini cho 80% cases (triều giá) ")
        print("     và chỉ escalate sang gpt-4o khi score gap > 1.0 → tiết kiệm ~35%.")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
