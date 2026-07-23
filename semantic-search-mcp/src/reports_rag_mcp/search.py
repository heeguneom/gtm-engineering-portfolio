"""Load the index and run semantic search via brute-force cosine similarity.

Per SPEC.md Decision #2: at this corpus scale (~1,800 chunks) a flat file plus
brute-force cosine similarity is simpler than a vector database and just as
fast. Per Decision #8: results below SIMILARITY_THRESHOLD are filtered out
rather than always returning top_k regardless of match quality.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from reports_rag_mcp.indexer import METADATA_FILENAME, VECTORS_FILENAME

SIMILARITY_THRESHOLD = 0.3


@dataclass(frozen=True)
class SearchResult:
    file: str
    heading: str
    snippet: str
    score: float


class IndexNotFoundError(RuntimeError):
    """Raised when semantic_search is called before any index has been built."""


class Index:
    def __init__(self, metadata: list[dict], vectors: np.ndarray) -> None:
        self._metadata = metadata
        self._vectors = vectors

    @classmethod
    def load(cls, index_dir: Path) -> "Index":
        metadata_path = index_dir / METADATA_FILENAME
        vectors_path = index_dir / VECTORS_FILENAME
        if not metadata_path.exists() or not vectors_path.exists():
            raise IndexNotFoundError(
                f"No index found at {index_dir}. Run reindex() first."
            )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        vectors = np.load(vectors_path)
        return cls(metadata, vectors)

    def __len__(self) -> int:
        return len(self._metadata)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> list[SearchResult]:
        if len(self._metadata) == 0:
            return []

        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        vector_norms = self._vectors / (
            np.linalg.norm(self._vectors, axis=1, keepdims=True) + 1e-10
        )
        scores = vector_norms @ query_norm

        ranked_indices = np.argsort(-scores)
        results: list[SearchResult] = []
        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score < threshold:
                break  # scores are sorted descending, so we can stop early
            entry = self._metadata[idx]
            results.append(
                SearchResult(
                    file=entry["file"],
                    heading=entry["heading"],
                    snippet=entry["text"],
                    score=score,
                )
            )
        return results


def embed_query(query: str) -> np.ndarray:
    from reports_rag_mcp.indexer import _get_model

    model = _get_model()
    embedding = model.encode([query], show_progress_bar=False, convert_to_numpy=True)
    return np.asarray(embedding[0], dtype=np.float32)
