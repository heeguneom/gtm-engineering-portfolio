---
title: Prior art — embedding-based link suggestion in PKM tools
sources:
  - type: web
    note: 4 parallel web probes (broad survey, entity/player scan, UX/threshold deep-dive, contrarian+recency) via /worldmodel dispatch, 2026-07-20
confidence: MEDIUM-HIGH (per-item confidence noted; most triangulated across 2+ probes, some single-channel)
---

# Prior art: how existing tools suggest links between notes

## The closest direct precedents (Obsidian plugins)

| Tool | Model | Level | UX pattern | Threshold/limits | Confidence |
|---|---|---|---|---|---|
| **Smart Connections** (`brianpetro/obsidian-smart-connections`) | Local (bge-micro-v2 default, zero setup) | Note-level default; block-level is a **paid-tier toggle** | 3 surfaces: auto-updating sidebar "Connections View," on-demand "Lookup," inline pop-over badges. **Suggest-only** — drag to insert, never auto-inserts. Ships a "Hide" feature to suppress noise as vaults grow | Not published, user-configurable | HIGH (triangulated) |
| **Semantic Backlinks** (`brightwav3/semantic-backlinks`) | Local (Ollama/LM Studio, e.g. bge-m3) or OpenAI API | Not fully specified | Inline popup while typing + sidebar panel | **The only tool with a published numeric default: 0.35 cosine threshold, max 10 popup results, 12-entry sidebar panel, 4-char minimum** | HIGH (triangulated) |
| **Semantic Auto-Linker** (`ysf-ad/semantic-auto-linker`) | Local (Transformers.js default) | Not fully specified | Whole-vault scan → review modal with **live graph-change preview before writing**. Closest match to this project's exact proposed shape (scan vault for unlinked similar-note pairs, suggest, review-before-write) | Not published | MEDIUM (single-channel) |
| **Similar Notes** (`joybro/obsidian-similar-notes`) | Local, **`all-MiniLM-L6-v2`** (same model this codebase already uses), Transformers.js/WebGPU, Orama vector DB | Note-level | Auto-displays top-5 similar notes at bottom of active note. **Already solves the "filter against already-linked" problem** — explicitly distinguishes already-linked vs. unlinked matches | Not published, fixed top-5 | MEDIUM (single-channel) |

Two more names surfaced but are easy to confuse: **"Semantic Linker"** (a
different, lighter plugin — metadata-only titles/tags/filenames matching, no
embeddings at all) vs. **"Semantic Auto-Linker"** (the embedding-based one
above). Don't conflate them.

## Non-Obsidian comparables (lower relevance, surveyed for breadth)

- **org-similarity** (TF-IDF/BM25, non-embedding) vs. **org-roam-similarity**
  (embedding-based, Jina AI, local) — same Emacs/org-roam ecosystem, same
  embedding-vs-lexical fork this project faces.
- **Reflect "AI Backlinks"** — on-demand (not automatic) command, replaces
  selected text with inline backlinks. Methodology undocumented publicly.
- Logseq, Notion AI, Mem, Heptabase, RemNote, Tana, Foam, Athens, Roam —
  surveyed, mostly fold this into a chat/Q&A layer rather than a discrete
  link-suggestion surface, or lack a comparable feature.

## Convergent patterns across the survey

1. **Suggest-only dominates; auto-insert is the outlier.** Every tool with a
   documented rationale (Smart Connections, Semantic Backlinks, Semantic
   Auto-Linker, Similar Notes, a MotherDuck/DuckDB DIY blog post, an Obsidian
   forum thread, an enterprise document-linking product's docs) requires
   human review before a link is written. The one auto-insert counter-example
   (Mem AI) is marketing copy with no stated design rationale. **This is the
   strongest, most consistent signal in the whole survey.**
2. **No industry-standard numeric threshold exists.** Only Semantic Backlinks
   publishes one (0.35 cosine / top-10 / 12-panel). Smart Connections leaves
   it configurable with no default; Notion AI uses an LLM re-ranker instead
   of a fixed cutoff. This codebase's own `semantic_search` threshold (0.3,
   Decision #8) is a reasonable starting anchor but was tuned for
   query-relevance, not permanent-edit-confidence — the two may reasonably
   want different values.
3. **Chunk-level vs. file-level is a live, unresolved fork industry-wide.**
   Smart Connections ships both as a toggle rather than picking one. The one
   detailed DIY precedent (MotherDuck/DuckDB Obsidian RAG blog) does
   chunk-level similarity directly for "hidden connection" discovery and
   never rolls up to file-level. No academic or vendor source settles
   max-pool vs. mean-pool vs. best-chunk-pair aggregation for this specific
   use case.
4. **Failure-mode narrative is thin, not confirmed-absent.** Four different
   search framings ("why I stopped using AI backlinks," "false positives,"
   "Smart Connections criticism," "AI second brain noise") turned up almost
   no substantive post-mortem content. One vendor admission (Smart
   Connections docs: "as vaults grow, some connections may be technically
   related but not useful," with a "Hide" feature as mitigation) is the only
   concrete data point. **This is a genuinely underdocumented area, not a
   solved problem** — treat "will this be noisy in practice" as a real open
   risk, not a dismissed one.

## Notable convergence with this specific codebase

`joybro/obsidian-similar-notes` defaults to **the exact same embedding model**
(`all-MiniLM-L6-v2`) this codebase already uses, and it already solves the
"filter against already-linked notes" problem this codebase's schema has no
mechanism for today. Worth treating as the single closest reference
implementation, model-compatibility-wise, even though it's not directly
reusable (different language/runtime, and this project hand-rolls per its own
G3 learning-goal decision).

## Adjacent, not directly on-point

- **Karpathy's "LLM Wiki" pattern** — an agent that ingests sources and
  writes/maintains an interlinked markdown wiki + schema doc, explicitly
  framed as *not* RAG. Shares the "use AI infra to build structure over time"
  framing that motivated this project's pivot, but is materially larger scope
  (an LLM authors pages, not just suggests links between human-written ones).
  MEDIUM confidence — one HN thread + gist, not yet an established pattern.
- **Andy Matuschak's critique** that backlinks are "weak peripheral vision" —
  a structural argument about link-list UX, not embedding mechanics. Relevant
  to how suggestions get *displayed*, not how they're computed.
