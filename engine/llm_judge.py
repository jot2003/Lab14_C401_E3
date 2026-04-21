import asyncio
import json
import os
import re
from statistics import median
from typing import Dict, Any, List, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

class LLMJudge:
    def __init__(
        self,
        judge_models: List[str] | None = None,
        disagreement_threshold: float = 1.0,
        use_live_judges: bool = True,
    ):
        if load_dotenv:
            load_dotenv()

        env_judges = [m.strip() for m in os.getenv("JUDGE_MODELS", "").split(",") if m.strip()]
        self.judge_models = judge_models or env_judges or ["gpt-4o", "gpt-4o-mini"]
        self.disagreement_threshold = disagreement_threshold
        self.client = None
        self.live_judging_enabled = False

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if use_live_judges and AsyncOpenAI and api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            self.live_judging_enabled = True

        self.rubrics = {
            "accuracy": 0.6,
            "completeness": 0.3,
            "professionalism": 0.1,
        }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", (text or "").lower())

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(1.0, min(5.0, value))

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        raw = (text or "").strip()
        if not raw:
            return {}

        if raw.startswith("```"):
            blocks = raw.split("```")
            if len(blocks) >= 2:
                raw = blocks[1].strip()
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()

        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _normalize_subscore(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0

        if score > 1.0:
            score = score / 5.0
        return round(max(0.0, min(1.0, score)), 3)

    def _judge_bias(self, judge_name: str) -> float:
        judge = judge_name.lower()
        if "mini" in judge:
            return -0.1
        if "gpt-4o" in judge:
            return 0.05
        return 0.0

    def _score_one_judge_heuristic(self, judge_name: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        q_tokens = set(self._tokenize(question))
        a_tokens = set(self._tokenize(answer))
        gt_tokens = set(self._tokenize(ground_truth))

        overlap = len(a_tokens & gt_tokens) / max(1, len(gt_tokens))
        completeness = min(1.0, len(a_tokens) / max(1, len(gt_tokens)))
        relevance = len(a_tokens & q_tokens) / max(1, len(q_tokens))

        weighted = (
            self.rubrics["accuracy"] * overlap
            + self.rubrics["completeness"] * completeness
            + self.rubrics["professionalism"] * relevance
        )
        raw_score = 1.0 + 4.0 * weighted + self._judge_bias(judge_name)
        final_score = round(self._clamp_score(raw_score), 2)

        return {
            "judge": judge_name,
            "score": final_score,
            "source": "heuristic_local",
            "subscores": {
                "accuracy": round(overlap, 3),
                "completeness": round(completeness, 3),
                "relevance": round(relevance, 3),
            },
        }

    async def _score_one_judge_live(self, judge_name: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        system_prompt = (
            "You are an impartial evaluator for RAG answer quality. "
            "Score the answer from 1 to 5 using the rubric below and return JSON only."
        )

        user_prompt = (
            "Rubric weights:\n"
            "- accuracy: 0.6\n"
            "- completeness: 0.3\n"
            "- professionalism: 0.1\n\n"
            "Return strict JSON object with keys:"
            " score, subscores, rationale.\n"
            "- score: number from 1 to 5\n"
            "- subscores: object with accuracy, completeness, professionalism in [0,1]\n"
            "- rationale: concise reason\n\n"
            f"Question:\n{question}\n\n"
            f"Ground truth:\n{ground_truth}\n\n"
            f"Candidate answer:\n{answer}"
        )

        completion = await self.client.chat.completions.create(
            model=judge_name,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        payload = self._extract_json(completion.choices[0].message.content or "")

        try:
            score_value = float(payload.get("score", 1.0))
        except (TypeError, ValueError):
            score_value = 1.0
        score = round(self._clamp_score(score_value), 2)

        subs = payload.get("subscores") if isinstance(payload.get("subscores"), dict) else {}
        subscores = {
            "accuracy": self._normalize_subscore(subs.get("accuracy")),
            "completeness": self._normalize_subscore(subs.get("completeness")),
            "professionalism": self._normalize_subscore(subs.get("professionalism")),
        }

        return {
            "judge": judge_name,
            "score": score,
            "source": "openai_api",
            "subscores": subscores,
            "rationale": str(payload.get("rationale", ""))[:400],
        }

    async def _score_one_judge(self, judge_name: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        if self.live_judging_enabled and self.client:
            try:
                return await self._score_one_judge_live(judge_name, question, answer, ground_truth)
            except Exception as exc:
                fallback = self._score_one_judge_heuristic(judge_name, question, answer, ground_truth)
                fallback["source"] = "heuristic_fallback"
                fallback["fallback_reason"] = str(exc)[:200]
                return fallback

        fallback = self._score_one_judge_heuristic(judge_name, question, answer, ground_truth)
        fallback["fallback_reason"] = "OPENAI_API_KEY missing or live judge disabled"
        return fallback

    def _resolve_disagreement(self, scores: List[float]) -> Tuple[float, float, float, str, bool]:
        max_gap = max(scores) - min(scores)
        agreement = max(0.0, 1.0 - (max_gap / 4.0))

        if max_gap > self.disagreement_threshold:
            final_score = float(median(scores))
            method = "median_for_conflict"
            requires_manual_review = True
        else:
            final_score = sum(scores) / len(scores)
            method = "mean"
            requires_manual_review = False

        return round(final_score, 2), round(agreement, 3), round(max_gap, 3), method, requires_manual_review

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """Evaluate one answer with multiple judges and resolve disagreement deterministically."""
        if not answer or not answer.strip():
            return {
                "final_score": 1.0,
                "agreement_rate": 1.0,
                "max_score_gap": 0.0,
                "conflict_resolved_by": "mean",
                "requires_manual_review": False,
                "individual_scores": {judge: 1.0 for judge in self.judge_models},
                "judge_details": [
                    {
                        "judge": judge,
                        "score": 1.0,
                        "source": "empty_answer_default",
                        "subscores": {"accuracy": 0.0, "completeness": 0.0, "professionalism": 0.0},
                    }
                    for judge in self.judge_models
                ],
            }

        tasks = [self._score_one_judge(judge_name, question, answer, ground_truth) for judge_name in self.judge_models]
        judge_details = await asyncio.gather(*tasks)
        scores = [item["score"] for item in judge_details]
        final_score, agreement, max_gap, resolution_method, requires_review = self._resolve_disagreement(scores)

        return {
            "final_score": final_score,
            "agreement_rate": agreement,
            "max_score_gap": max_gap,
            "conflict_resolved_by": resolution_method,
            "requires_manual_review": requires_review,
            "individual_scores": {item["judge"]: item["score"] for item in judge_details},
            "judge_details": judge_details,
        }

    async def check_position_bias(self, response_a: str, response_b: str):
        """Return a simple symmetric bias estimate based on response-length shift."""
        len_a = len((response_a or "").strip())
        len_b = len((response_b or "").strip())
        total = max(1, len_a + len_b)
        bias_score = abs(len_a - len_b) / total
        return {
            "position_bias_score": round(bias_score, 3),
            "is_position_biased": bias_score > 0.35,
        }
