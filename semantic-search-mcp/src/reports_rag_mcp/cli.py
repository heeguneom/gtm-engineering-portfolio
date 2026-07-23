"""Standalone CLI entry point for rebuilding the index, independent of MCP.

Usage: uv run reindex
"""

from __future__ import annotations

from reports_rag_mcp.server import INDEX_DIR, VAULT_ROOT
from reports_rag_mcp.indexer import build_index


def main() -> None:
    stats = build_index(VAULT_ROOT, INDEX_DIR)
    # This is a standalone CLI process, not the MCP server — stdout is safe here.
    print(
        f"files_processed={stats.files_processed} "
        f"files_skipped={stats.files_skipped} "
        f"chunks_total={stats.chunks_total} "
        f"duration_s={stats.duration_s:.1f}"
    )


if __name__ == "__main__":
    main()
