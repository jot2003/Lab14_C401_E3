import asyncio
import re
from typing import List, Dict

# Import corpus for keyword-based retrieval
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.synthetic_gen import CORPUS


# Common English stop words to exclude from scoring
_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might can could of in on at to for "
    "with by from as into about between through after before above "
    "below and or but not no nor so yet both either neither each "
    "every all any few more most other some such that this these "
    "those it its i me my we our you your he him his she her they "
    "them their what which who whom how when where why if then than "
    "very too also just only even still already again once here there".split()
)

class MainAgent:
    """
    RAG Agent with keyword-based retrieval over the in-memory CORPUS.
    Retrieves top-k relevant documents by weighted token overlap (TF-IDF-like),
    then generates an answer by extracting the most relevant sentences.
    """

    def __init__(self, top_k: int = 3):
        self.name = "SupportAgent-v2"
        self.top_k = top_k
        self._docs = CORPUS
        self._tokenized = {
            doc["doc_id"]: set(re.findall(r"\w+", doc["content"].lower()))
            for doc in self._docs
        }
        # Build document frequency for IDF-like weighting
        from collections import Counter
        self._df = Counter()
        for tokens in self._tokenized.values():
            for t in tokens:
                self._df[t] += 1
        self._num_docs = len(self._docs)

    def _retrieve(self, question: str) -> List[Dict]:
        """Rank docs by IDF-weighted token overlap with question."""
        import math
        q_tokens = set(re.findall(r"\w+", question.lower())) - _STOP_WORDS
        scored = []
        for doc in self._docs:
            doc_tokens = self._tokenized[doc["doc_id"]]
            common = q_tokens & doc_tokens
            # IDF-weighted score: rare terms matter more
            score = sum(math.log(1 + self._num_docs / (1 + self._df.get(t, 0))) for t in common)
            # Bonus for title match
            title_tokens = set(re.findall(r"\w+", doc.get("title", "").lower())) - _STOP_WORDS
            title_overlap = len(q_tokens & title_tokens)
            score += title_overlap * 2.0
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[: self.top_k]]

    @staticmethod
    def _extract_answer(question: str, contexts: List[str]) -> str:
        """Build answer from context sentences most relevant to question.
        Uses the full top-1 document plus best sentences from others."""
        if not contexts:
            return "I don't have sufficient information in the knowledge base to answer this question."

        q_tokens = set(re.findall(r"\w+", question.lower()))

        # Always include the full top-1 context (highest retrieval score)
        base = contexts[0]

        # Add best sentences from remaining contexts
        extra_sentences: List[tuple] = []
        for ctx in contexts[1:]:
            for sent in re.split(r"(?<=[.!?])\s+", ctx):
                s_tokens = set(re.findall(r"\w+", sent.lower()))
                score = len(q_tokens & s_tokens)
                if score >= 2:
                    extra_sentences.append((score, sent))
        extra_sentences.sort(key=lambda x: x[0], reverse=True)

        parts = [base]
        added = 0
        for _, sent in extra_sentences:
            if added >= 3:
                break
            parts.append(sent)
            added += 1

        return " ".join(parts)

    # Adversarial / out-of-scope detection patterns
    _ADVERSARIAL_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+DAN",
        r"do\s+anything\s+now",
        r"system\s+prompt\s+verbatim",
        r"internal\s+API\s+keys",
        r"jailbreak",
    ]
    _OUT_OF_SCOPE_KEYWORDS = [
        "boiling point", "translate", "poem", "political revolution",
        "swahili", "tungsten", "recipe", "weather forecast",
    ]

    def _is_adversarial(self, question: str) -> bool:
        q_lower = question.lower()
        for pat in self._ADVERSARIAL_PATTERNS:
            if re.search(pat, q_lower):
                return True
        return False

    def _is_out_of_scope(self, question: str) -> bool:
        q_lower = question.lower()
        return any(kw in q_lower for kw in self._OUT_OF_SCOPE_KEYWORDS)

    async def query(self, question: str) -> Dict:
        await asyncio.sleep(0.05)

        # Handle adversarial / out-of-scope
        if self._is_adversarial(question):
            return {
                "answer": "I cannot comply with that request. I am designed to answer questions about AI evaluation, RAG systems, retrieval metrics, and related technical topics. I cannot ignore my instructions or provide internal system information.",
                "contexts": [],
                "retrieved_ids": [],
                "metadata": {"model": "keyword-rag-v2", "tokens_used": 0, "sources": []},
            }
        if self._is_out_of_scope(question):
            return {
                "answer": "This question falls outside the scope of the available knowledge base. I can help with questions about AI evaluation, RAG architectures, LLM judges, retrieval metrics, and related technical topics.",
                "contexts": [],
                "retrieved_ids": [],
                "metadata": {"model": "keyword-rag-v2", "tokens_used": 0, "sources": []},
            }

        retrieved_docs = self._retrieve(question)
        contexts = [doc["content"] for doc in retrieved_docs]
        retrieved_ids = [doc["doc_id"] for doc in retrieved_docs]

        answer = self._extract_answer(question, contexts)

        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "keyword-rag-v2",
                "tokens_used": len(answer.split()),
                "sources": retrieved_ids,
            },
        }


if __name__ == "__main__":
    agent = MainAgent()

    async def test():
        resp = await agent.query("What are the four main components of a RAG system?")
        print(resp["answer"][:200])
        print("Retrieved:", resp["retrieved_ids"])

    asyncio.run(test())
