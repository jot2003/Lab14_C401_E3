# Day14 - Task priority and execution flow (today)

This file answers:
- What must be done first to avoid blockers?
- Which outputs unlock downstream tasks?
- What merge flow keeps risk low today?

---

## 1) Priority map
- `P0` `D14-T01`: Generate valid golden dataset.
- `P0` `D14-T02`: Confirm retrieval metrics (Hit Rate, MRR).
- `P0` `D14-T03`: Complete multi-judge consensus path.
- `P0` `D14-T04`: Run regression gate and write failure analysis.
- `P0` `D14-T05`: Final quality gate and submission readiness.

`P1`:
- Improve async performance and evaluation cost tracking details.

`P2`:
- Polish report language and reflection depth.

---

## 2) Critical dependencies
1. `D14-T01` must finish before reliable benchmarking.
2. `D14-T02` needs dataset cases from `D14-T01`.
3. `D14-T03` depends on stable runner outputs from `D14-T02`.
4. `D14-T04` depends on final metrics from `D14-T02` and `D14-T03`.
5. `D14-T05` runs only after all required artifacts are updated.

---

## 3) End-to-end execution flow
1. Generate dataset:
   - `python data/synthetic_gen.py`
2. Execute benchmark:
   - `python main.py`
3. Validate submission format:
   - `python check_lab.py`
4. Review outputs:
   - `reports/benchmark_results.json`
   - `reports/summary.json`
   - `analysis/failure_analysis.md`
5. Apply fixes if needed and repeat the same 3-command cycle.

---

## 4) Merge order
1. `D14-T01` dataset branch
2. `D14-T02` retrieval metrics branch
3. `D14-T03` multi-judge branch
4. `D14-T04` regression + failure analysis branch
5. `D14-T05` integration and final gate branch

For each merge:
- Pull latest target branch first.
- Resolve conflicts immediately with owning task members.
- Re-run `python main.py` and `python check_lab.py`.

---

## 5) Stop/go criteria for submission

Go only when all are true:
- Golden dataset exists and passes structural checks.
- Benchmark report and summary report are regenerated today.
- Failure analysis is updated with concrete root causes.
- No blocking errors from `python check_lab.py`.

Otherwise: stop submission, assign fix owner, rerun full validation cycle.
