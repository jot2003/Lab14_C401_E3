# Reflection — Nguyen Thanh Nam (D14-T04: Regression Gate & Failure Analysis)

## Task Summary
Owned `main.py` regression logic and `analysis/failure_analysis.md` — responsible for V1/V2 comparison, release gate decisions, and root cause analysis.

## What I Did
- Implemented `run_regression_gate()` with 5 threshold checks: avg_score ≥ 3.0, hit_rate ≥ 0.8, agreement_rate ≥ 0.7, manual_review_rate ≤ 0.1, and score delta ≥ -0.05.
- Built V1 (single judge baseline) vs V2 (multi-judge optimized) comparison pipeline.
- Implemented `CostReport` dataclass with per-model cost breakdown and per-case cost estimation.
- Added `GateThresholds` dataclass for configurable, auditable threshold management.
- Wrote comprehensive failure analysis with 5-Whys for the 3 worst-performing cases.
- Identified failure clustering: 100% of failures trace to agent stub + ID mismatch root causes.

## What Went Well
- Regression gate correctly identifies ROLLBACK when V2 avg_score (2.944) < 3.0 minimum threshold, even though delta (+0.076) is positive.
- Multi-gate approach prevents false releases: passing 4/5 checks is not enough if quality floor is breached.
- Cost analysis provides actionable data: $0.00143/case, $0.076 total for 53 cases.
- Failure analysis correctly identifies the agent stub as the single root cause blocking all improvements.

## Challenges
- V1 baseline uses only 1 judge (GPT-4o-mini), making V1-V2 comparison not fully apples-to-apples.
- All 53 cases fail for the same root cause, so failure clustering doesn't reveal diverse failure modes.
- Threshold values (e.g., min_avg_score=3.0) are somewhat arbitrary without historical data to calibrate against.

## What I Learned
- A regression gate is only as good as its baseline — if V1 is also broken, comparing V1 vs V2 doesn't tell you much.
- 5-Whys analysis is most valuable when failures are diverse; systematic failures point to infrastructure issues, not algorithmic ones.
- Cost tracking from day one creates accountability and enables optimization decisions later.

## If I Had More Time
- Would implement historical trend tracking to calibrate thresholds based on actual performance distributions.
- Would add per-difficulty regression analysis (easy/medium/hard breakdowns).
- Would build a dashboard for visualizing regression trends over time.
