"""Build the semantic search index: chunk the vault, embed locally, write to disk.

Per SPEC.md Decision #1/#2/#5/#10(superseded): local sentence-transformers
embeddings, flat JSON+.npy storage (no vector DB), plain full rebuild on every
call (no incremental/mtime-skip logic — that was deliberately reverted).

CRITICAL: this module must never print to stdout — see SPEC.md §13. All
progress/diagnostic output goes to stderr via the `logging` module.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from reports_rag_mcp.chunking import Chunk, chunk_file

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
METADATA_FILENAME = "metadata.json"
VECTORS_FILENAME = "vectors.npy"

logger = logging.getLogger("reports_rag_mcp.indexer")
if not logger.handlers:
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class IndexStats:
    files_processed: int
    files_skipped: int
    chunks_total: int
    duration_s: float


_model_cache: dict[str, object] = {}


def _get_model():
    """Lazily load the embedding model (avoids paying the load cost at import time)."""
    if EMBEDDING_MODEL_NAME not in _model_cache:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s ...", EMBEDDING_MODEL_NAME)
        _model_cache[EMBEDDING_MODEL_NAME] = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model_cache[EMBEDDING_MODEL_NAME]


def collect_chunks(vault_root: Path) -> tuple[list[Chunk], int, int]:
    """Walk vault_root for .md files and chunk each one.

    Returns (chunks, files_processed, files_skipped). A file that fails to
    read/parse is skipped and logged (to stderr) rather than aborting the
    whole rebuild.
    """
    chunks: list[Chunk] = []
    files_processed = 0
    files_skipped = 0

    for path in sorted(vault_root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            file_chunks = chunk_file(path, vault_root)
        except (OSError, UnicodeError) as exc:
            logger.warning("Skipping %s: %s", path, exc)
            files_skipped += 1
            continue
        chunks.extend(file_chunks)
        files_processed += 1

    return chunks, files_processed, files_skipped


def build_index(vault_root: Path, index_dir: Path) -> IndexStats:
    """Full rebuild: chunk the vault, embed every chunk, write index atomically.

    No incremental/mtime-skip logic by design (SPEC.md Decision #10,
    superseded) — every call re-chunks and re-embeds the entire vault. Napkin
    math in the spec shows this is well under 2 minutes at current scale.
    """
    start = time.monotonic()
    chunks, files_processed, files_skipped = collect_chunks(vault_root)

    if chunks:
        model = _get_model()
        texts = [c.text for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        embeddings = np.asarray(embeddings, dtype=np.float32)
    else:
        embeddings = np.zeros((0, 0), dtype=np.float32)

    index_dir.mkdir(parents=True, exist_ok=True)
    metadata = [
        {"file": c.file_path, "heading": c.heading, "text": c.text} for c in chunks
    ]

    metadata_tmp = index_dir / f".{METADATA_FILENAME}.tmp"
    # Must end in .npy: np.save() silently appends .npy to any filename that
    # doesn't already have it, which would break the exact rename target below.
    vectors_tmp = index_dir / ".vectors.tmp.npy"
    metadata_tmp.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    np.save(vectors_tmp, embeddings)

    # Atomic replace: rename only after both temp files are fully written.
    metadata_tmp.replace(index_dir / METADATA_FILENAME)
    vectors_tmp.replace(index_dir / VECTORS_FILENAME)

    duration_s = time.monotonic() - start
    logger.info(
        "Index rebuilt: %d files processed, %d skipped, %d chunks, %.1fs",
        files_processed,
        files_skipped,
        len(chunks),
        duration_s,
    )
    return IndexStats(
        files_processed=files_processed,
        files_skipped=files_skipped,
        chunks_total=len(chunks),
        duration_s=duration_s,
    )
