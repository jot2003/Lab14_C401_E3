import asyncio
import re
from statistics import median
from typing import Dict, Any, List, Tuple

class LLMJudge:
    def __init__(self, judge_models: List[str] | None = None, disagreement_threshold: float = 1.0):
        self.judge_models = judge_models or ["gpt-4o", "claude-3-5"]
        self.disagreement_threshold = disagreement_threshold
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

    def _judge_bias(self, judge_name: str) -> float:
        judge = judge_name.lower()
        if "claude" in judge:
            return -0.2
        if "gpt" in judge:
            return 0.1
        return 0.0

    def _score_one_judge(self, judge_name: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
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
            "subscores": {
                "accuracy": round(overlap, 3),
                "completeness": round(completeness, 3),
                "relevance": round(relevance, 3),
            },
        }

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
                    {"judge": judge, "score": 1.0, "subscores": {"accuracy": 0.0, "completeness": 0.0, "relevance": 0.0}}
                    for judge in self.judge_models
                ],
            }

        judge_details = [
            self._score_one_judge(judge_name, question, answer, ground_truth)
            for judge_name in self.judge_models
        ]
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
