from __future__ import annotations
from typing import List, Dict, Any
import math

# Types
from langchain_core.documents import Document

# -------- Cross-Encoder Reranker --------
class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str | None = None):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, question: str, docs: List[Document], top_n: int) -> List[Document]:
        if not docs:
            return docs
        pairs = [(question, d.page_content) for d in docs]
        # batch predict to avoid OOM on big candidate sets
        scores = self._predict_batched(pairs, batch_size=64)
        rescored = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [d for d, _ in rescored[:top_n]]

    def _predict_batched(self, pairs, batch_size: int = 64):
        scores = []
        for i in range(0, len(pairs), batch_size):
            chunk = pairs[i:i+batch_size]
            scores.extend(self.model.predict(chunk))
        return scores

# -------- LLM Reranker (Gemini as judge) --------
class LLMReranker:
    def __init__(self, llm):
        self.llm = llm

    def rerank(self, question: str, docs: List[Document], top_n: int) -> List[Document]:
        if not docs:
            return docs
        scored = []
        # one LLM call per doc (simple, reliable). For speed you could also pack multiple in one prompt.
        for d in docs:
            snippet = d.page_content[:1200]  # keep the prompt short
            prompt = (
                "You are scoring candidate context for a question.\n"
                f"Question: {question}\n"
                f"Candidate text:\n{snippet}\n\n"
                "Return ONLY a number 0-10 for relevance."
            )
            try:
                score_txt = self.llm.complete(prompt)
                # robust parse: pull first float-ish token
                token = "".join(ch for ch in score_txt if (ch.isdigit() or ch in ".- "))
                score = float(token.strip().split()[0]) if token.strip() else 0.0
            except Exception:
                score = 0.0
            scored.append((d, float(score)))
        rescored = sorted(scored, key=lambda x: x[1], reverse=True)
        return [d for d, _ in rescored[:top_n]]

# -------- Factory --------
def build_reranker(cfg: Dict[str, Any], llm=None):
    rtype = (cfg.get("type") or "none").lower()
    if rtype == "cross_encoder":
        model = cfg.get("model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        return CrossEncoderReranker(model_name=model)
    if rtype == "llm":
        if llm is None:
            raise ValueError("LLM reranker selected but no llm client passed")
        return LLMReranker(llm)
    return None
