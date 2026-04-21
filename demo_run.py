import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_step(title: str, command: list[str]) -> None:
    print(f"\n=== {title} ===")
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {title} (exit code {result.returncode})")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def summarize_results(summary: dict, benchmark: list[dict]) -> None:
    metrics = summary.get("metrics", {})
    metadata = summary.get("metadata", {})
    regression = summary.get("regression", {})
    gate = regression.get("gate_decision", "UNKNOWN")

    total = int(metadata.get("total", 0))
    pass_count = int(metrics.get("pass_count", 0))
    fail_count = int(metrics.get("fail_count", 0))
    review_count = sum(1 for x in benchmark if x.get("status") == "review")

    print("\n=== DEMO SUMMARY ===")
    print(f"Total cases         : {total}")
    print(f"Average score (1-5) : {metrics.get('avg_score')}")
    print(f"Pass/Fail/Review    : {pass_count}/{fail_count}/{review_count}")
    print(f"Pass rate           : {metrics.get('pass_rate')}")
    print(f"Hit rate            : {metrics.get('hit_rate')}")
    print(f"Agreement rate      : {metrics.get('agreement_rate')}")
    print(f"Manual review rate  : {metrics.get('manual_review_rate')}")
    print(f"Gate decision       : {gate}")

    print("\n=== MODEL COMPARISON (JUDGE AVG SCORE) ===")
    model_scores = metrics.get("judge_model_avg_scores", {})
    for model, score in sorted(model_scores.items()):
        print(f"- {model:12} : {score}")

    print("\n=== SUBMISSION ARTIFACT CHECK ===")
    required = [
        ROOT / "reports" / "summary.json",
        ROOT / "reports" / "benchmark_results.json",
        ROOT / "analysis" / "failure_analysis.md",
    ]
    for path in required:
        status = "OK" if path.exists() else "MISSING"
        print(f"- {path.relative_to(ROOT)} : {status}")


def score_comment(avg_score: float, pass_rate: float) -> None:
    print("\n=== QUICK INTERPRETATION ===")
    if avg_score >= 3.5 and pass_rate >= 0.7:
        print("Current quality is GOOD for demo and submission.")
    elif avg_score >= 3.0:
        print("Current quality PASSES gate, but there is room to optimize.")
    else:
        print("Current quality is BELOW release threshold; optimize before demo.")

    print("Scale note: avg_score is on a 1-5 scale.")
    print("Your current target should be: keep avg_score >= 3.0 and agreement >= 0.7.")


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    run_step("Generate dataset", ["python", "data/synthetic_gen.py"])
    run_step("Run benchmark and gate", ["python", "main.py"])
    run_step("Run submission checker", ["python", "check_lab.py"])

    summary = load_json(ROOT / "reports" / "summary.json")
    benchmark = load_json(ROOT / "reports" / "benchmark_results.json")
    summarize_results(summary, benchmark)

    metrics = summary.get("metrics", {})
    score_comment(float(metrics.get("avg_score", 0.0)), float(metrics.get("pass_rate", 0.0)))

    print("\nDone. You can now demo using this summary output.")


if __name__ == "__main__":
    main()
