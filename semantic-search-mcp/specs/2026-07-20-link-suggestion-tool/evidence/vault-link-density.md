---
title: Vault wiki-link density (the pivot trigger)
sources:
  - path: ~/.claude/reports (561 .md files, grep -rohE)
    type: direct-measurement
confidence: HIGH
---

# Finding: the vault has almost no existing `[[wiki-link]]` graph

Measured directly via `grep -rohE '\[\[[^]]+\]\]'` across all 561 `.md` files in
`~/.claude/reports`:

- **4 of 561 files** contain any `[[...]]` syntax at all.
- **20 total occurrences**, but most are documentation examples showing link
  syntax (`[[Page]]`, `[[Page#Heading]]`, `[[Page|Display]]`) inside docs that
  *explain* wiki-links, not actual links to other documents.
- **Only 2 are genuine cross-document links**: `[[CAREER-OPS-HANDOFF]]` and
  `[[APPLICATIONS]]`.

## Implication

The original spec seed ("fuse RAG with the Obsidian knowledge graph that
already exists in this vault") rests on a false premise for this specific
corpus. There is no meaningful author-built graph to fuse with — 559 of 561
files have zero real links. This is what triggered the pivot from "GraphRAG
fusion" (Option A) to "RAG-assisted link suggestion" (Option B, chosen).

## Also confirmed: no link-parsing exists in the codebase either

`chunking.py` was read in full — it contains only a heading regex
(`^(#{1,6})\s+(.*)$`). No `[[...]]` parsing, no frontmatter parsing, nothing
link-related. The graph doesn't exist in the data, and there's no code that
would extract it if it did.
