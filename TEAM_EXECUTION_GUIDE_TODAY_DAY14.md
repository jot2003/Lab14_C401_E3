# Day14 Team Execution Guide - How we finish today

## 1) Session objective
- Deliver a working AI Evaluation Factory aligned with rubric.
- Ensure all mandatory artifacts are generated from real runs.
- Keep the pipeline reproducible by any teammate.

## 2) Timebox plan (4 hours)
- Sprint 1 (0:00-0:45): Golden dataset generation and sanity checks.
- Sprint 2 (0:45-2:15): Eval engine validation (retrieval + multi-judge + async runner).
- Sprint 3 (2:15-3:15): Benchmark run, regression comparison, failure clustering.
- Sprint 4 (3:15-4:00): Final optimization, report completion, submission checks.

## 3) Definition of done by workstream

## Dataset and SDG
- `data/golden_set.jsonl` has >=50 valid cases.
- Cases include question, expected answer signal, and ground-truth ids.
- No duplicate or invalid jsonl lines.

## Retrieval evaluation
- Hit Rate and MRR are both computed and persisted.
- Retrieval outputs can be traced per case for debugging.
- Metrics are visible in `reports/benchmark_results.json`.

## Multi-judge consensus
- At least two judge signals are present for each case.
- Conflict resolution path is deterministic.
- Agreement metric is included in summary/report.

## Regression and release gate
- Run comparison between baseline and current configuration.
- Gate decision is explicit: release or rollback.
- Decision rationale is written in report outputs.

## Failure analysis and reflection
- `analysis/failure_analysis.md` includes practical 5-Whys sections.
- Each member has an updated reflection file in `analysis/reflections/`.

## 4) Team handoff checklist
- [ ] Pull latest branch state before starting.
- [ ] Run local task checks before opening PR/merge request.
- [ ] Attach evidence (metric diff, run logs, or report snippet).
- [ ] Notify next dependent owner immediately after completion.

## 5) Final command checklist
```bash
python data/synthetic_gen.py
python main.py
python check_lab.py
```

If `check_lab.py` fails, fix format/completeness first, then re-run full checks.

## 6) Commit naming suggestion
- `feat(day14): ...`
- `fix(day14): ...`
- `docs(day14): ...`
- `chore(day14): ...`

Include task id in commit body, for example `D14-T03`.
