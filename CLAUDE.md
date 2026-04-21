# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An AI Evaluation Factory — a team-based benchmarking pipeline for RAG (Retrieval-Augmented Generation) agents. The system generates synthetic test datasets, runs agents against them, evaluates quality with RAGAS and multi-model LLM judges, and produces regression reports to approve or block deployments.

## Setup & Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Generate golden dataset (required before running evaluation)
python data/synthetic_gen.py

# Run the full evaluation pipeline
python main.py

# Validate submission format
python check_lab.py
```

Requires a `.env` file with API keys (not committed). `data/golden_set.jsonl` must exist before `main.py` will run.

## Architecture

### Pipeline Flow

```
data/synthetic_gen.py → data/golden_set.jsonl
                              ↓
                         main.py
                         ├── agent/main_agent.py  (RAG agent under test)
                         ├── engine/runner.py      (orchestration)
                         ├── engine/retrieval_eval.py
                         └── engine/llm_judge.py
                              ↓
                    reports/summary.json
                    reports/benchmark_results.json
```

### Key Modules

**`engine/runner.py` — BenchmarkRunner**  
Central orchestrator. `run_all()` batch-processes test cases with `asyncio.gather()` (default `batch_size=5` to avoid rate limits). Each `run_single_test()` call returns latency, RAGAS scores, and judge results.

**`engine/retrieval_eval.py` — RetrievalEvaluator**  
Computes retrieval quality: `calculate_hit_rate()` checks if expected doc IDs appear in top-k results; `calculate_mrr()` computes Mean Reciprocal Rank.

**`engine/llm_judge.py` — LLMJudge**  
Multi-model consensus evaluation using ≥2 judge models (GPT-4o, Claude-3.5). Returns `final_score` (1–5 scale) and `agreement_rate`. Includes conflict resolution logic.

**`agent/main_agent.py` — MainAgent**  
Placeholder RAG agent. Replace with the real implementation. Interface: `async query(question) → {answer, contexts, metadata}`.

**`main.py`**  
Runs V1_Base vs V2_Optimized comparison, computes deltas on `avg_score`, `hit_rate`, and `agreement_rate`, then applies a release gate (approve if V2 ≥ V1).

### Per-Test Result Schema

```json
{
  "agent_response": "...",
  "latency": 1.23,
  "ragas": {
    "faithfulness": 0.9,
    "relevancy": 0.85,
    "retrieval": { "hit_rate": 0.8, "mrr": 0.75 }
  },
  "judge": {
    "final_score": 4,
    "agreement_rate": 0.9,
    "individual_scores": [4, 4]
  },
  "status": "pass"
}
```

`status` is `"pass"` when `final_score >= 3`.

### Golden Dataset Format (`data/golden_set.jsonl`)

One JSON object per line:
```json
{
  "question": "...",
  "expected_answer": "...",
  "context": "...",
  "metadata": { "difficulty": "hard", "type": "adversarial", "expected_retrieval_ids": ["doc_1"] }
}
```

Includes adversarial cases: prompt injection, hallucination triggers, out-of-context questions, and conflicting information.

## Team Task Ownership

| Task | Owner | Responsibility |
|------|-------|---------------|
| D14-T01 | Dang Dinh Tu Anh | Dataset SDG (`data/synthetic_gen.py`) |
| D14-T02 | Quach Gia Duoc | Retrieval Metrics (`engine/retrieval_eval.py`) |
| D14-T03 | Pham Quoc Dung | Multi-Judge Consensus (`engine/llm_judge.py`) |
| D14-T04 | Nguyen Thanh Nam | Regression & Failure Analysis |
| D14-T05 | Hoang Kim Tri Thanh | Final Integration & Submission |

## Grading Weights

- Retrieval evaluation: 15%
- Multi-judge reliability: 20%
- Performance/cost analysis: 15%
- Root cause / failure analysis: 20%

Required submission artifacts: `reports/summary.json`, `reports/benchmark_results.json`, `analysis/failure_analysis.md`.
