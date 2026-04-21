# Reflection — Quach Gia Duoc (D14-T02: Retrieval Metrics)

## Task Summary
Owned `engine/retrieval_eval.py` — responsible for implementing Hit Rate and MRR (Mean Reciprocal Rank) retrieval quality metrics.

## What I Did
- Implemented `calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)` — returns 1.0 if any expected document appears in top-k retrieved results.
- Implemented `calculate_mrr(expected_ids, retrieved_ids)` — returns reciprocal of the rank of the first matching document.
- Built `evaluate_batch()` to process entire datasets and compute aggregate `avg_hit_rate` and `avg_mrr`.
- Integrated retrieval metrics into `BenchmarkRunner.run_single_test()` so per-case hit_rate and mrr flow through to reports.

## What Went Well
- Clean separation between retrieval evaluation and the rest of the pipeline.
- Metrics are well-defined and follow standard IR evaluation conventions (HR@k, MRR).
- Results show Hit Rate = 1.0 in the RAGAS retrieval sub-score, confirming the metric pipeline works end-to-end.

## Challenges
- ID format mismatch between golden dataset (`doc_rag_intro`) and agent output (`policy_handbook.pdf`) — the agent stub returns hardcoded filenames instead of logical document IDs.
- Per-case `hit_rate` and `mrr` in benchmark_results show `null` because the runner computes them via RAGAS retrieval sub-scores rather than directly from my evaluator methods in some paths.

## What I Learned
- Retrieval metrics are only meaningful when the ID scheme is consistent across the entire pipeline (dataset → vector store → agent output → evaluator).
- Hit Rate is a coarse metric (binary per query); MRR provides more granular signal about ranking quality.
- Integration testing across module boundaries is as important as unit correctness.

## If I Had More Time
- Would implement NDCG@k for a more nuanced ranking metric.
- Would add per-difficulty-level retrieval analysis to identify where retrieval fails most.
- Would standardize the ID scheme with a shared mapping module.
