from __future__ import annotations

import faiss
import numpy as np


class SemanticSearchService:
    def __init__(self) -> None:
        self.index = None
        self.documents: list[dict] = []

    def _embed(self, text: str, dim: int = 128) -> np.ndarray:
        vector = np.zeros(dim, dtype="float32")
        for token in text.lower().split():
            vector[hash(token) % dim] += 1.0
        norm = np.linalg.norm(vector)
        return vector if norm == 0 else vector / norm

    def build_index(self, documents: list[dict]) -> dict:
        self.documents = documents
        vectors = (
            np.vstack([self._embed(doc["content"]) for doc in documents]).astype("float32")
            if documents
            else np.empty((0, 128), dtype="float32")
        )
        self.index = faiss.IndexFlatIP(128)
        if len(vectors):
            self.index.add(vectors)
        return {"indexed_documents": len(documents), "dimension": 128}

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.index is None or not self.documents:
            return []
        query_vector = self._embed(query).reshape(1, -1)
        scores, indices = self.index.search(query_vector, top_k)
        results = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
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
