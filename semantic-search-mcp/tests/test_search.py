import json

import numpy as np
import pytest

from reports_rag_mcp.indexer import METADATA_FILENAME, VECTORS_FILENAME
from reports_rag_mcp.search import Index, IndexNotFoundError, SIMILARITY_THRESHOLD


def _make_index(entries: list[tuple[str, str, str, list[float]]]) -> Index:
    metadata = [
        {"file": file, "heading": heading, "text": text}
        for file, heading, text, _ in entries
    ]
    vectors = np.array([vec for *_rest, vec in entries], dtype=np.float32)
    return Index(metadata, vectors)


def test_ranks_by_cosine_similarity_descending():
    index = _make_index(
        [
            ("a.md", "A", "close match", [1.0, 0.0]),
            ("b.md", "B", "orthogonal", [0.0, 1.0]),
            ("c.md", "C", "near match", [0.9, 0.1]),
        ]
    )
    query = np.array([1.0, 0.0], dtype=np.float32)

    results = index.search(query, top_k=3, threshold=0.0)

    assert [r.file for r in results] == ["a.md", "c.md", "b.md"]
    assert results[0].score > results[1].score > results[2].score


def test_filters_results_below_similarity_threshold():
    index = _make_index(
        [
            ("a.md", "A", "close match", [1.0, 0.0]),
            ("b.md", "B", "orthogonal, unrelated", [0.0, 1.0]),
        ]
    )
    query = np.array([1.0, 0.0], dtype=np.float32)

    results = index.search(query, top_k=5, threshold=0.5)

    assert len(results) == 1
    assert results[0].file == "a.md"


def test_default_threshold_matches_spec_decision_8():
    assert SIMILARITY_THRESHOLD == pytest.approx(0.3)


def test_no_match_returns_empty_list_not_weak_top_k():
    index = _make_index([("a.md", "A", "totally different topic", [0.0, 1.0])])
    query = np.array([1.0, 0.0], dtype=np.float32)

    results = index.search(query, top_k=5, threshold=0.5)

    assert results == []


def test_empty_index_returns_empty_list():
    index = Index(metadata=[], vectors=np.zeros((0, 2), dtype=np.float32))
    query = np.array([1.0, 0.0], dtype=np.float32)

    assert index.search(query, top_k=5) == []


def test_respects_top_k_limit():
    entries = [
        (f"{i}.md", f"H{i}", "text", [1.0, 0.0]) for i in range(10)
    ]
    index = _make_index(entries)
    query = np.array([1.0, 0.0], dtype=np.float32)

    results = index.search(query, top_k=3, threshold=0.0)

    assert len(results) == 3


def test_load_raises_clear_error_when_index_missing(tmp_path):
    with pytest.raises(IndexNotFoundError):
        Index.load(tmp_path / "does-not-exist")


def test_load_round_trips_a_written_index(tmp_path):
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    metadata = [{"file": "a.md", "heading": "A", "text": "hello"}]
    vectors = np.array([[1.0, 0.0]], dtype=np.float32)
    (index_dir / METADATA_FILENAME).write_text(json.dumps(metadata), encoding="utf-8")
    np.save(index_dir / VECTORS_FILENAME, vectors)

    index = Index.load(index_dir)

    assert len(index) == 1
