# Day14 - Team task allocation for today (AI Evaluation Factory)

## Goal
- Finish a complete evaluation cycle for Lab14 in one session.
- Produce valid artifacts: `data/golden_set.jsonl`, `reports/benchmark_results.json`, `reports/summary.json`, `analysis/failure_analysis.md`.
- Keep work split by clear ownership to reduce merge conflicts.

## Team members
1. Hoang Kim Tri Thanh (2A202600372)
2. Dang Dinh Tu Anh (2A202600019)
3. Quach Gia Duoc (2A202600423)
4. Pham Quoc Dung (2A202600490)
5. Nguyen Thanh Nam (2A202600205)

## Working rules
1. One owner per task and one reviewer buddy.
2. Each task touches only its declared files unless owner confirms.
3. Before handoff, run local verification for that task scope.
4. No final merge before `python check_lab.py` passes.

## Task allocation

| Task ID | Owner | Main files | Scope | Required output |
|---|---|---|---|---|
| D14-T01 | Dang Dinh Tu Anh | `data/synthetic_gen.py`, `data/golden_set.jsonl` | Build/refresh SDG flow, ensure >=50 high quality cases with ground truth doc ids | Stable dataset generated, no malformed jsonl lines |
| D14-T02 | Quach Gia Duoc | `engine/retrieval_eval.py`, `engine/runner.py` | Validate Hit Rate + MRR calculation and retrieval logging | Retrieval metrics appear in benchmark outputs |
| D14-T03 | Pham Quoc Dung | `engine/llm_judge.py`, `engine/runner.py` | Multi-judge consensus and agreement handling | At least 2 judge results + agreement metric in report |
| D14-T04 | Nguyen Thanh Nam | `main.py`, `reports/summary.json`, `analysis/failure_analysis.md` | Regression gate logic and 5-Whys failure writeup | Clear release/rollback decision and root-cause analysis |
| D14-T05 | Hoang Kim Tri Thanh | `check_lab.py`, `README.md`, `analysis/reflections/` | Final integration gate, run full pipeline, collect team evidence | Submission-ready repository and checklist pass |

## Quick incident ownership
- Dataset generation issue -> `D14-T01`
- Retrieval metric mismatch -> `D14-T02`
- Judge disagreement/format issue -> `D14-T03`
- Release gate/report inconsistency -> `D14-T04`
- Final packaging/check failure -> `D14-T05`

## Shared commands (must run today)
```bash
python data/synthetic_gen.py
python main.py
python check_lab.py
```
