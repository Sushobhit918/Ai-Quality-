from __future__ import annotations

import hashlib
import math


class SemanticSearchService:
    """Small dependency-free hashed-vector search for repository snippets.

    This intentionally uses the Python standard library instead of FAISS so
    the API function stays within serverless bundle-size limits.
    """

    def __init__(self) -> None:
        self.vectors: list[list[float]] = []
        self.documents: list[dict] = []

    def _embed(self, text: str, dim: int = 128) -> list[float]:
        vector = [0.0] * dim
        for token in text.lower().split():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "little") % dim
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def build_index(self, documents: list[dict]) -> dict:
        self.documents = documents
        self.vectors = [self._embed(doc["content"]) for doc in documents]
        return {"indexed_documents": len(documents), "dimension": 128}

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.vectors or not self.documents or top_k <= 0:
            return []

        query_vector = self._embed(query)
        ranked = []
        for index, vector in enumerate(self.vectors):
            score = sum(left * right for left, right in zip(query_vector, vector))
            ranked.append((score, index))

        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, index in ranked[:top_k]:
            document = self.documents[index]
            results.append(
                {
                    "score": float(score),
                    "type": document["type"],
                    "path": document.get("path"),
                    "content": document["content"][:300],
                }
            )
        return results
