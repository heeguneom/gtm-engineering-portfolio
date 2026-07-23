"""FastMCP server exposing semantic_search and reindex over ~/.claude/reports.

Per SPEC.md Decision #6/#9: this server is additive to (not a replacement
for) the existing `obsidian` MCP server — it only ever reads the vault, never
writes/edits/moves/deletes report files (that stays obsidian-mcp's job).

CRITICAL: stdio-mode MCP servers must never write to stdout (SPEC.md §13) —
all logging in this module and its dependencies goes to stderr.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastmcp import FastMCP

from reports_rag_mcp.indexer import build_index
from reports_rag_mcp.linking import suggest_links as _suggest_links
from reports_rag_mcp.search import Index, IndexNotFoundError, embed_query

VAULT_ROOT = Path(os.environ.get("REPORTS_RAG_VAULT_ROOT", str(Path.home() / ".claude" / "reports")))
INDEX_DIR = Path(os.environ.get("REPORTS_RAG_INDEX_DIR", str(Path.home() / "dev" / "reports-rag-mcp" / "index_data")))

mcp = FastMCP("reports-rag")


@mcp.tool
def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """Semantically search the ~/.claude/reports vault and return the most
    relevant chunks for a natural-language query.

    Results below a similarity threshold are filtered out rather than
    returned as weak/irrelevant matches — an empty list means no relevant
    report was found, not that the index is broken.

    Returns a list of {file, heading, snippet, score}, most relevant first.
    """
    try:
        index = Index.load(INDEX_DIR)
    except IndexNotFoundError as exc:
        raise RuntimeError(
            f"{exc} Call reindex() first to build the index."
        ) from exc

    query_embedding = embed_query(query)
    results = index.search(query_embedding, top_k=top_k)
    return [
        {"file": r.file, "heading": r.heading, "snippet": r.snippet, "score": r.score}
        for r in results
    ]


@mcp.tool
def reindex() -> dict:
    """Rebuild the semantic search index from the current state of
    ~/.claude/reports. Full rebuild every call (no incremental logic, by
    design — see SPEC.md Decision #10). Takes well under 2 minutes at the
    current corpus size.

    Returns {files_processed, files_skipped, chunks_total, duration_s}.
    """
    stats = build_index(VAULT_ROOT, INDEX_DIR)
    return {
        "files_processed": stats.files_processed,
        "files_skipped": stats.files_skipped,
        "chunks_total": stats.chunks_total,
        "duration_s": round(stats.duration_s, 1),
    }


@mcp.tool
def suggest_links(top_k: int = 10) -> list[dict]:
    """Suggest [[wiki-link]] candidates between semantically-close files in
    ~/.claude/reports that aren't currently linked to each other.

    Uses per-file centroid embeddings (mean-pooled from each file's existing
    chunk vectors -- no new embedding cost) compared file-to-file. Already
    linked pairs are excluded via fail-open wiki-link resolution: an
    ambiguous or unresolvable link target is never treated as "already
    linked" (a redundant suggestion is a cheaper mistake than a silently
    suppressed real one).

    Suggest-only: this tool never writes to any file. To actually insert a
    confirmed link, use the obsidian-mcp server's edit-note tool.

    Returns a list of {file_a, file_b, score}, most similar first.
    """
    try:
        index = Index.load(INDEX_DIR)
    except IndexNotFoundError as exc:
        raise RuntimeError(
            f"{exc} Call reindex() first to build the index."
        ) from exc

    results = _suggest_links(index, top_k=top_k)
    return [{"file_a": r.file_a, "file_b": r.file_b, "score": r.score} for r in results]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
