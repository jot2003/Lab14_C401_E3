# Reflection — Dang Dinh Tu Anh (D14-T01: Dataset SDG)

## Task Summary
Owned `data/synthetic_gen.py` — responsible for generating the golden evaluation dataset with ≥50 synthetic test cases covering normal and adversarial scenarios.

## What I Did
- Designed a 12-document corpus covering RAG architecture, RAGAS metrics, retrieval evaluation, LLM judging, regression testing, hallucination detection, chunking, cost optimization, failure analysis, and position bias.
- Generated 45 normal cases (easy/medium/hard) with ground-truth retrieval IDs mapped to corpus documents.
- Created 8 adversarial red-teaming cases: prompt injection, goal hijacking, out-of-context, ambiguous, conflicting information, multi-hop reasoning, and correction scenarios.
- Total: 53 valid JSONL entries with complete `question`, `expected_answer`, `context`, and `metadata` fields.
- Added `--openai` flag for optional LLM-augmented generation and `--count N` for target count control.

## What Went Well
- Dataset exceeded the 50-case minimum requirement.
- Adversarial cases cover OWASP-style prompt injection patterns and edge cases that stress-test agent robustness.
- Ground-truth `expected_retrieval_ids` are logically mapped to corpus document IDs, enabling meaningful retrieval evaluation.

## Challenges
- Balancing difficulty distribution (easy/medium/hard) to avoid ceiling or floor effects in scoring.
- Ensuring adversarial cases have well-defined expected answers (e.g., "I don't know" for out-of-context).
- Coordinating ID scheme (`doc_*` logical IDs) with the retrieval pipeline's actual document naming.

## What I Learned
- Synthetic data generation quality directly determines evaluation validity — garbage in, garbage out.
- Adversarial test design requires understanding both the agent's capabilities and its failure modes.
- A well-structured corpus with clear document boundaries makes retrieval evaluation much more interpretable.

## If I Had More Time
- Would add OpenAI-augmented paraphrase variants to increase diversity.
- Would implement stratified sampling to ensure balanced coverage across difficulty levels and question types.
- Would add multi-hop questions that require reasoning across 3+ documents.
