# Reflection — Pham Quoc Dung (D14-T03: Multi-Judge Consensus)

## Task Summary
Owned `engine/llm_judge.py` — responsible for implementing multi-model LLM judge consensus with conflict resolution.

## What I Did
- Implemented `LLMJudge` with support for 2+ judge models (GPT-4o, GPT-4o-mini).
- Built dual scoring paths: `_score_one_judge_live()` (OpenAI API) and `_score_one_judge_heuristic()` (token-overlap fallback).
- Implemented conflict resolution: mean aggregation when judges agree (gap ≤ 1.0), median when they disagree (gap > 1.0).
- Added `agreement_rate` metric: `1.0 - (max_gap / 4.0)`, providing a 0–1 scale of judge consensus.
- Added `requires_manual_review` flag for cases with high disagreement.
- Implemented `check_position_bias()` method for detecting ordering effects in judge evaluations.
- Built weighted rubric scoring with accuracy (0.6), completeness (0.3), and professionalism (0.1) sub-scores.

## What Went Well
- Agreement rate of 96.3% across 53 cases shows the two judges are highly consistent.
- Conflict resolution logic correctly distinguishes between consensus (mean) and disagreement (median) scenarios.
- Manual review rate of 0.0% indicates no cases triggered the disagreement threshold.
- Heuristic fallback ensures the pipeline never crashes even without API keys.

## Challenges
- Heuristic scoring uses token overlap, which doesn't capture semantic similarity — leads to low accuracy sub-scores (avg 0.056).
- Completeness sub-score is biased by answer length rather than content coverage, causing false positives (1.0 for placeholder answers).
- Judge bias parameters (GPT-4o: +0.05, GPT-4o-mini: -0.1) are hand-tuned, not empirically calibrated.

## What I Learned
- Multi-judge consensus is critical for evaluation reliability — a single judge can be systematically biased.
- The gap between heuristic and LLM-based evaluation is enormous; token overlap is a poor proxy for answer quality.
- Position bias detection is important but rarely triggered when both judges use similar scoring rubrics.

## If I Had More Time
- Would calibrate judge bias parameters using a held-out validation set.
- Would implement a cascade strategy: GPT-4o-mini first, escalate to GPT-4o only when gap > threshold (35% cost savings).
- Would add per-rubric-dimension agreement analysis to identify which quality aspects judges disagree on most.
