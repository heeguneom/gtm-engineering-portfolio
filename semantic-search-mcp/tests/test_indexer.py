import json

import numpy as np
import pytest

from reports_rag_mcp.indexer import METADATA_FILENAME, VECTORS_FILENAME, build_index, collect_chunks


@pytest.fixture
def vault(tmp_path):
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "a.md").write_text("# Topic A\nfacts about topic a\n", encoding="utf-8")
    (vault_root / "daily.md").write_text("no headings, just a daily note\n", encoding="utf-8")
    sub = vault_root / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("# Topic B\nfacts about topic b\n", encoding="utf-8")
    return vault_root


def test_collect_chunks_walks_subdirectories(vault):
    chunks, files_processed, files_skipped = collect_chunks(vault)

    assert files_processed == 3
    assert files_skipped == 0
    file_paths = {c.file_path for c in chunks}
    assert file_paths == {"a.md", "daily.md", "sub/b.md"}


def test_collect_chunks_ignores_non_markdown_files(tmp_path):
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "notes.md").write_text("# Notes\ncontent\n", encoding="utf-8")
    (vault_root / "image.png").write_bytes(b"\x89PNG\r\n")

    chunks, files_processed, _ = collect_chunks(vault_root)

    assert files_processed == 1
    assert all(c.file_path == "notes.md" for c in chunks)


@pytest.mark.slow
def test_build_index_writes_metadata_and_vectors_atomically(vault, tmp_path):
    index_dir = tmp_path / "index"

    stats = build_index(vault, index_dir)

    assert stats.files_processed == 3
    assert stats.files_skipped == 0
    assert stats.chunks_total == 3
    assert stats.duration_s >= 0

    metadata_path = index_dir / METADATA_FILENAME
    vectors_path = index_dir / VECTORS_FILENAME
    assert metadata_path.exists()
    assert vectors_path.exists()
    # no leftover temp files from the atomic-replace step
    assert not any(index_dir.glob(".*"))

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    vectors = np.load(vectors_path)
    assert len(metadata) == 3
    assert vectors.shape[0] == 3


@pytest.mark.slow
def test_rebuild_excludes_deleted_files_no_orphan_entries(vault, tmp_path):
    """Regression test for the exact scenario the audit caught (SPEC.md
    Decision #10 supersession): a plain full rebuild must never leave stale
    index entries pointing at files that no longer exist.
    """
    index_dir = tmp_path / "index"
    build_index(vault, index_dir)

    (vault / "a.md").unlink()
    stats = build_index(vault, index_dir)

    assert stats.files_processed == 2
    metadata = json.loads((index_dir / METADATA_FILENAME).read_text(encoding="utf-8"))
    file_paths = {entry["file"] for entry in metadata}
    assert "a.md" not in file_paths
    assert file_paths == {"daily.md", "sub/b.md"}


@pytest.mark.slow
def test_unreadable_file_is_skipped_not_fatal(vault, tmp_path, monkeypatch):
    from reports_rag_mcp import chunking

    original_chunk_file = chunking.chunk_file

    def flaky_chunk_file(path, vault_root):
        if path.name == "daily.md":
            raise OSError("simulated read failure")
        return original_chunk_file(path, vault_root)

    monkeypatch.setattr("reports_rag_mcp.indexer.chunk_file", flaky_chunk_file)

    index_dir = tmp_path / "index"
    stats = build_index(vault, index_dir)

    assert stats.files_skipped == 1
    assert stats.files_processed == 2
