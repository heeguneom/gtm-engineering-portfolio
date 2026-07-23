---
title: reports-rag-mcp current architecture and locked precedents
sources:
  - path: src/reports_rag_mcp/chunking.py
    type: direct-read
  - path: src/reports_rag_mcp/indexer.py
    type: direct-read
  - path: src/reports_rag_mcp/search.py
    type: direct-read
  - path: src/reports_rag_mcp/server.py
    type: direct-read
  - path: specs/reports-rag-mcp/SPEC.md
    type: direct-read
confidence: HIGH
---

# reports-rag-mcp: what exists today and what's locked

## Pipeline (four modules)

1. **`chunking.py`** — splits markdown by heading (`#`-`######`), 600-word cap
   per chunk, fixed-size window fallback for headless files. Pure regex, no
   link/frontmatter parsing. `Chunk = {file_path, heading, text}`.
2. **`indexer.py`** — walks vault, embeds all chunks via local
   `sentence-transformers` (`all-MiniLM-L6-v2`, cached in `_model_cache`),
   writes flat `metadata.json` (list of `{file, heading, text}`) +
   `vectors.npy` atomically (`.tmp` write + `Path.replace()`). **Full rebuild
   every call — no incremental/mtime-skip logic.**
3. **`search.py`** — loads the flat index, brute-force cosine similarity
   (`vector_norms @ query_norm`), filters below `SIMILARITY_THRESHOLD = 0.3`,
   returns ranked `SearchResult(file, heading, snippet, score)`.
4. **`server.py`** — FastMCP server, two tools: `semantic_search(query,
   top_k=5)` and `reindex()`. Reads vault/index paths from env vars
   (`REPORTS_RAG_VAULT_ROOT`, `REPORTS_RAG_INDEX_DIR`) with home-relative
   fallbacks.

## Locked precedents (from specs/reports-rag-mcp/SPEC.md Decision Log) relevant to any new feature

| # | Decision | Why it constrains a link-suggestion feature |
|---|---|---|
| 1 | `all-MiniLM-L6-v2`, local, no paid API | Any suggestion feature reuses this embedding, doesn't introduce a new model |
| 2 | Flat file storage (JSON + `.npy`), no vector DB | A suggestions artifact should follow the same flat-file convention |
| 5 | On-demand rebuild only, no live file-watching | A suggestion computation triggered "automatically" on file save is off the table without reopening this decision |
| 6 | Coexist with `obsidian-mcp`, never write to vault files | reports-rag-mcp is **read-only** on the vault. Any flow that writes `[[links]]` into a file must cross into `obsidian-mcp`'s `edit-note` tool — a different MCP server entirely |
| 8 | Low-similarity results filtered, not always returned | Precedent for a suggestion feature also needing a confidence cutoff, though the right threshold may differ from search's 0.3 (see design-fork evidence file) |
| 10 (superseded) | mtime-aware incremental skip was proposed, then **reverted** after a design-challenge audit found the promotion was speculative, not evidence-driven | Direct precedent: don't add complexity to a link-suggestion computation (e.g. incremental suggestion updates) without an observed-annoyance trigger, per this repo's own established bar |

## Hard constraints inherited by any new code in `indexer.py`/`server.py`

- **stdout is forbidden** — stdio-mode MCP servers corrupt the JSON-RPC stream
  if anything writes to stdout. All logging must go to `stderr` via the
  `logging` module. `cli.py` is the one exception (standalone process).
- **Atomic writes** — `.tmp` file + `Path.replace()`, never a direct
  overwrite, to avoid a reader seeing a partially-written index.

## The chunk-level vs. file-level gap

The index is **chunk-level only** — `metadata.json` has one entry per chunk,
no file-level embedding or file-level record exists anywhere. A "these two
*files* are similar" signal doesn't exist today; it would need to be either
derived (aggregate chunk-pair scores) or built fresh (new file-level embedding
pass, roughly doubling embedding volume per reindex). This is a genuine open
design fork — see `prior-art-pkm-link-suggestion.md` for how other tools
handle it.

## obsidian-mcp's actual tool surface (verified from the installed package, not inferred)

Read directly from `~/.npm/_npx/1eddcb5200a425a4/node_modules/obsidian-mcp/README.md`
(v1.0.6). 12 tools: `read-note`, `create-note`, `edit-note`, `move-note`,
`delete-note`, `create-directory`, `search-vault`, `add-tags`, `remove-tags`,
`rename-tag`, `manage-tags`, `list-available-vaults`. **No backlinks/graph
tool exists.** Confirms this isn't something reports-rag-mcp would be
duplicating — the capability genuinely doesn't exist anywhere in the current
toolchain.
