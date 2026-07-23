# Link Suggestion Tool for reports-rag-mcp — Spec

**Status:** Approved
**Owner(s):** HeeGun Eom
**Last updated:** 2026-07-20
**Baseline commit:** 0962921
**Links:**
- Base project spec: `../reports-rag-mcp/SPEC.md`
- Evidence: `./evidence/`
- Changelog: `./meta/_changelog.md`

---

## 1) Problem statement

**Situation:** `reports-rag-mcp` gives Claude semantic recall over HeeGun's 561-file vault (`~/.claude/reports`), solving "find conceptually related content by meaning." The vault also supports Obsidian-style `[[wiki-links]]` for deliberate, author-built structure between documents, exposed today via a separate `obsidian-mcp` server that can read/write notes but has no link-suggestion or graph capability.

**Complication:** The vault has almost no real link structure — only 2 of 561 files contain a genuine `[[link]]` to another document (`evidence/vault-link-density.md`). The original idea for this spec ("fuse RAG with the vault's existing knowledge graph") assumed a graph that doesn't exist. Building fusion machinery against a 99.6%-unlinked corpus would deliver near-zero value today. The vault also grows continuously via the `technical-research` skill (base spec, `specs/reports-rag-mcp/SPEC.md` §12: roughly a few reports/week) — real, confirmed growth, not a speculative scaling concern.

**Resolution:** Invert the original idea. Use the embeddings `reports-rag-mcp` already computes to *suggest* `[[wiki-links]]` between semantically-close, currently-unlinked documents — helping build a real graph over time rather than assuming one exists. This reuses existing infrastructure (no new embedding model, no new 3P dependency) and is consistent with how the strongest prior art in this space (Smart Connections, Semantic Auto-Linker, Similar Notes — `evidence/prior-art-pkm-link-suggestion.md`) frames the same problem: suggest, review, let a human confirm.

## 2) Goals
- G1: Given the existing chunk embeddings, surface candidate `[[link]]` pairs between files that are semantically close but not currently linked.
- G2: Reuse existing infrastructure — same embedding model, same flat-file storage convention, no new paid service (inherits the base project's NG3 constraint).
- G3: Suggestions are reviewable before any file is edited — no silent auto-linking (matches the dominant pattern in prior art and this codebase's read-only-on-vault boundary, Decision 6).

## 3) Non-goals
- **[NOT NOW]** NG1: Auto-inserting suggested links without human/Claude review. — Revisit if: usage proves review-step friction is the actual bottleneck, with real evidence (matches this repo's own evidence-before-complexity bar, e.g. Decision #10's reversion).
- **[NOT NOW]** NG2: Real-time/automatic suggestion computation on file save (would require reopening the base spec's Decision #5, on-demand-only rebuild). — Revisit if: batch/on-demand suggestion generation proves too infrequent in practice.
- **[NOT UNLESS]** NG3: File-level embeddings as a separate embedding pass. — Only if: both cheaper pooling tiers prove inadequate first — file-centroid pooling (D2, v1) and, if that's too coarse, chunk-pair max-pool (Future Work escalation) — since prior art is split on whether pooling suffices at all (Smart Connections ships both as a toggle) and doubling embedding volume isn't worth paying for speculatively before the cheaper tiers are tried.
- **[NEVER]** NG4: reports-rag-mcp writing directly to vault files. Inherited, LOCKED constraint from the base spec (Decision 6) — any file write crosses into `obsidian-mcp`'s `edit-note`, a different MCP server.

## 4) Personas / consumers
- P1: HeeGun, via Claude Code, same consumption shape as the existing `semantic_search`/`reindex` tools.

## 5) User journeys

**P1 happy path:**
1. HeeGun or Claude calls `suggest_links(top_k=10)` — any time after an index exists, independent of when the last `reindex()` ran.
2. Tool computes file-pair scores in-memory (per-file centroid of existing chunk embeddings, D2), filters out pairs already linked (parsed from index text with fail-open resolution, D5/D6) and below the 0.5 threshold (D3), returns ranked `{file_a, file_b, score}`.
3. Claude presents suggestions to HeeGun.
4. HeeGun responds to that specific suggestion (accept/reject); only on explicit per-suggestion acceptance does Claude use `obsidian-mcp`'s `edit-note` to insert the `[[link]]` — crosses the server boundary, reports-rag-mcp itself never writes (NG4). No standing instruction skips this per-suggestion confirmation — matches NG1's stricter reading and keeps G3's "reviewable, no silent auto-linking" guarantee unambiguous.

**Failure / recovery path:**
- No index exists yet → same failure mode as `semantic_search` today (clear error directing to `reindex()` first).
- Vault has zero eligible pairs above threshold → empty result, not a forced weak suggestion (mirrors Decision #8's existing filter-don't-force-topk pattern).

**"Aha moment":** Claude surfaces a link between two reports HeeGun wrote months apart and forgot were related — validates G1.

### Interaction state matrix

| Feature / Surface | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| `suggest_links` MCP tool | N/A (measured milliseconds at file-level, D4) | No pairs above 0.5 threshold → empty list, not forced weak matches | Index missing → same error pattern as `semantic_search`, directs to `reindex()` | Ranked `{file_a, file_b, score}` pairs, already-linked pairs excluded (fail-open on ambiguous resolution, D6) | Index stale (reports added since last reindex) → suggestions only reflect last-indexed state, same staleness profile as `semantic_search` today, no new signal needed |

## 6) Requirements

### Functional requirements
| Priority | Requirement | Acceptance criteria | Notes |
|---|---|---|---|
| Must | Expose `suggest_links(top_k: int = 10) -> list[{file_a, file_b, score}]` as an MCP tool | Given an existing index, returns up to top_k candidate file pairs ranked by score, callable independent of `reindex()` | D1 |
| Must | Aggregate via file-level centroid, not chunk-pair max-pool | Each file's chunk vectors are mean-pooled into one centroid; file-pair score = cosine similarity between two files' centroids | D2 (superseded from chunk-pair max-pool 2026-07-20) |
| Must | Exclude self-pairs and deduplicate symmetric pairs | A file is never compared to itself; `(file_a, file_b)` and `(file_b, file_a)` return once — trivial at file granularity (`i < j` iteration guard) | Originally found during completeness re-sweep at chunk granularity; simplified by D2's move to file-level |
| Must | Recognize wiki-link syntax variants when parsing "already linked" | Parser matches `[[Target]]`, `[[Target\|Display]]`, and `[[Target#Heading]]` forms — the vault's own docs contain examples of all three (`evidence/vault-link-density.md`) | Found during completeness re-sweep |
| Must | Parse links from already-loaded index text, not a fresh disk read | "Already linked" detection groups chunk `text` by `file` from the loaded index, never re-reads `.md` files from disk | D5 |
| Must | Resolve wiki-link targets with a fail-open rule | Case-insensitive basename match (strip `.md`) against indexed file paths; zero or multiple matches → treat as unresolved, never suppress a suggestion on ambiguity | D6 — 73/561 files share a basename, verified directly |
| Must | Filter results below the suggestion threshold (default 0.5, tunable) | A file pair scoring below threshold is never returned | D3 |
| Must | Filter out pairs that are already linked | A suggestion is never surfaced for a pair where `[[link]]` already exists between the two files (either direction) | Requires new minimal `[[...]]` regex parser (Q6) — doesn't exist anywhere in the codebase today; mirrors `chunking.py`'s existing heading-regex pattern |
| Must | Compute in-memory at call time, no new persisted artifact | `index_data/` gains no new files; `indexer.py`/`reindex()` are untouched | D4 |
| Must | No silent auto-write to vault files | reports-rag-mcp itself never calls anything that edits a `.md` file | Inherits base spec Decision 6, NG4 |
| Must | Never write to stdout | All logging in any new module goes to stderr, matching `indexer.py`'s existing pattern (`server.py` itself does no logging today) | Inherited hard constraint (stdio MCP transport) |

### Non-functional requirements
- Performance: Milliseconds per call at current scale (561 files, measured directly — D4), and scale-robust going forward since cost tracks file count, not the faster-growing chunk count (already 11,536 and climbing).
- Reliability: Inherits base project's "fail loud, never silent-wrong" bar — missing index raises the same clear error `semantic_search` does today.
- Security/privacy: Inherits base project's local-only, no-data-leaves-machine requirement — no new dependency, no new network call.
- Cost: $0 — no new paid API/service (inherits NG3 from base spec).

## 7) Success metrics & instrumentation
- Metric 1: HeeGun actually accepts and inserts suggested links (qualitative — same self-reported-experience approach as the base project, no formal telemetry planned for a personal tool).

## 8) Current state (how it works today)
See `evidence/codebase-architecture.md` and `evidence/vault-link-density.md` for full detail. Summary:
- No link-suggestion capability exists anywhere in the toolchain (neither `reports-rag-mcp` nor `obsidian-mcp`).
- No `[[...]]` parsing exists in this codebase.
- The index is chunk-level only; no file-level similarity signal exists today.
- `obsidian-mcp` (separate server, read/write) has no backlinks/graph tool (verified from the installed package's own README).

## 9) Proposed solution (vertical slice)

### User experience / surfaces
- No UI — MCP tool surface only, same as the base project.
- New MCP tool `suggest_links(top_k=10)` registered in `server.py` alongside `semantic_search`/`reindex`.
- No CLI addition planned (unlike `reindex`, this isn't something HeeGun would run standalone outside a Claude session).

### System design
- **Architecture overview:** One new module, `linking.py`, sitting alongside `chunking.py`/`indexer.py`/`search.py`. It (1) loads the existing `Index` (reuses `search.py`'s `Index.load`), (2) groups already-loaded chunk `text` entries by `file` and parses `[[...]]` occurrences from that in-memory text — recognizing `[[Target]]`, `[[Target|Display]]`, `[[Target#Heading]]` — to build an "already linked" set, resolving each target to a file path via case-insensitive basename match, fail-open on zero/multiple matches (D5/D6), (3) computes each file's centroid vector by mean-pooling that file's chunk vectors, (4) computes the file×file cosine similarity matrix via the same normalize+matmul pattern `Index.search()` already uses, just at file rather than chunk granularity (D2), (5) filters self-pairs, deduplicates symmetric pairs (`i < j`), filters already-linked pairs and below-threshold pairs (D3), (6) returns ranked pairs. `server.py` gains one new `@mcp.tool` wrapping this.
- **Data model:** No new persisted schema — reuses `metadata.json`/`vectors.npy` as-is. In-memory only: per-file centroid vectors (561×384, derived fresh each call from the existing chunk vectors) and a `dict[(file_a, file_b), float]` of pair scores during a single call.
- **Transport:** Same FastMCP/stdio server, no new transport.
- **Auth/permissions:** None — same as base project (local process, local file access).
- **Enforcement point(s):** N/A.
- **Observability:** Any diagnostic logging goes to stderr, same as `indexer.py`.

### Alternatives considered
See `evidence/prior-art-pkm-link-suggestion.md` for the full survey.
- **Automatic/passive suggestion** (Smart Connections-style) — rejected: no live "note view" signal exists in this MCP/Claude Code context to trigger it from.
- **Reindex-coupled batch computation** — rejected: couples suggestion latency to reindex frequency for a feature that may be called much less often than reindex; on-demand keeps concerns separated (D1).
- **New file-level embeddings** (separate embedding pass) — deferred (NG3): doubles embedding cost per reindex; centroid pooling (D2, chosen) gets file-level comparison without any new embedding cost, so this is only worth revisiting if centroid quality proves inadequate.
- **Chunk-pair max-pool** — the original D2 choice, superseded 2026-07-20 after audit found it was 423x more expensive than believed (measured: 532MB/0.35s at the real 11,536-chunk scale vs. centroid's 1.3MB/milliseconds) and the corpus is already 6.4x past the base spec's original sizing assumption. Moved to Future Work as the escalation path if centroid suggestions prove too coarse — it still catches a buried niche idea in a long file that a whole-file centroid would dilute, a real trade-off being knowingly accepted, not overlooked.
- **No new tool at all** — rely on Claude ad hoc calling existing `semantic_search` per-file when relevant, zero new code. Rejected: G1 reads as requiring systematic, corpus-wide coverage; reproducing that via repeated single-file `semantic_search` calls would mean up to 561 sequential tool invocations with no principled threshold/dedup, expensive in tool-call volume and context budget — a cheaper partial substitute, not a comprehensive one.

---

## 10) Decision log

| ID | Decision | Type (P/T/X) | Resolution | 1-way door? | Rationale | Evidence / links | Implications |
|---|---|---|---|---|---|---|---|
| D1 | New dedicated on-demand MCP tool `suggest_links(top_k=10) -> [{file_a, file_b, score}]`, mirroring `semantic_search`'s style. No coupling to `reindex()`. "Automatic/passive" (live view-state) ruled out as not implementable in this architecture. | Technical | LOCKED | Yes (new public tool surface) — user explicitly confirmed | Matches locked on-demand philosophy (base spec Decision 5); matches strongest prior-art pattern (Semantic Auto-Linker's explicit-invoke-then-review); fully additive, zero change to existing tools | `evidence/prior-art-pkm-link-suggestion.md` | Requirements §6, journey §5, and proposed solution §9 all finalized around this shape |
| D2 | ~~Chunk-pair max-pool~~ **SUPERSEDED → file-level centroid aggregation**: mean-pool each file's existing chunk vectors into one centroid, compare file-to-file directly | Technical | DIRECTED | No | **Reopened 2026-07-20 via audit + design-challenge.** Original max-pool rationale (catches a buried niche idea in a long file) still holds as a real trade-off, but audit found D4's napkin math used a stale chunk count (assumed ~1,800; actual measured 11,536 — base spec's own vector-DB reopen trigger is "10x beyond ~1,800," and the corpus is already 6.4x past that baseline and still growing). Centroid aggregation reuses the same existing embeddings at zero new cost, is 423x cheaper (measured: 561²=315K comparisons vs 11,536²=133M), and mechanically removes 2 of the 3 Must-requirements the completeness re-sweep added (same-file exclusion and symmetric dedup become trivial at file granularity). Chunk-level max-pool moves to Future Work as the escalation path if centroid suggestions prove too coarse in practice | `meta/design-challenge.md` Finding 1, `meta/audit-findings.md` Findings 1-2, measured directly (see D4) | Loses buried-niche-idea detection — documented explicitly as an accepted trade-off, not silently dropped. §14 risk added |
| D3 | Suggestion similarity threshold starts at ~0.5 cosine, empirically tunable | Technical | DIRECTED | No | A wrong suggestion risks a permanent edit, costlier than a wrong search result (search's 0.3 was tuned for query-relevance, not edit-confidence); prior-art research found suggestion-noise risk genuinely underdocumented, so starting conservative is the safer direction, matching how base spec Decision #8 treated its own threshold as a tunable starting point. **Note:** threshold is now applied to file-centroid similarity (D2), not chunk-pair similarity — may need retuning once real centroid scores are observed, since centroid similarity is typically less extreme than best-chunk-pair similarity | `evidence/prior-art-pkm-link-suggestion.md` (only published number industry-wide is Semantic Backlinks' 0.35) | Exact value is DIRECTED not LOCKED — revisit after real usage, no spec reopen needed to tune it |
| D4 | No new persisted artifact — suggestions computed in-memory at call time from the existing index | Technical | LOCKED | No | **Corrected 2026-07-20:** original napkin math (~1,800 chunks, 13MB) was stale — actual index has 11,536 chunks (measured directly via `np.load('index_data/vectors.npy').shape`), and a full chunk-level all-pairs matrix actually measures 532MB / 0.35s (empirically run, not estimated). D2's move to file-level centroid aggregation resolves this: file-level all-pairs is 561×561, ~1.3MB, milliseconds — even cheaper than originally believed for chunk-level, and scale-robust as the vault keeps growing (file count grows far slower than chunk count) | Measured directly: `.venv/bin/python` matmul benchmark on real `vectors.npy`, 2026-07-20 | `indexer.py`/`reindex()` remain completely untouched; new code is additive-only (new module + new tool registration) |
| D5 | Parse "already linked" from the already-loaded index's chunk text (grouped by file), not a fresh disk read | Technical | DIRECTED | No | Avoids an unaccounted second full-vault I/O pass on every call; keeps both signals (link presence, similarity score) sourced from the same last-`reindex()` snapshot rather than mixing live-disk-state with frozen-index-state | `meta/design-challenge.md` Finding 3 | Accepted edge case: a link containing a space in display text (`[[Target\|Display Name]]`) could rarely straddle a 600-word chunk-window boundary; not mitigated, noted as a known limitation |
| D6 | Wiki-link target resolution: **full relative-path match first** (case-insensitive, `.md` optional), **falling back to basename match** for bare-title links; **fail open** on zero or multiple matches at either tier (never suppress a suggestion on ambiguous/unresolved match) | Technical | LOCKED | No | Verified directly: 73 of 561 files share a basename with another file (53 alone are named `REPORT.md`), so naive basename-only matching is genuinely ambiguous, not a rare edge case. **Corrected post-implementation:** the original basename-only resolver silently failed to recognize the full-path-style links (`[[folder/REPORT]]`) that a fail-open-aware writer actually uses for exactly these ambiguous files — found when a just-linked pair kept re-appearing in suggestions after reindex. Fixed to try full-path first, basename as fallback. A false "already linked" (wrongly suppressing a real gap) is still a worse failure than an occasional redundant suggestion, matching this spec's own "fail loud, never silent-wrong" bar | `meta/design-challenge.md` Finding 2; independently verified basename-collision count, 2026-07-20; resolver bug found + fixed via live re-verification, 2026-07-20 | Recognizes `[[Target]]`, `[[Target\|Display]]`, `[[Target#Heading]]` syntax variants per the completeness-re-sweep requirement, at both path and basename tiers |
| D7 | Exclude files matching `Resume-` (basename substring) from suggestion consideration entirely, on either side of a pair | Technical | LOCKED | No | **Added post-implementation, from live validation.** First real `suggest_links()` run against the actual 11,536-chunk index returned 14 of top-15 results as tailored-resume pairs (0.97-1.0 score) — the template/boilerplate-similarity risk named in §14 confirmed real and initially dominant. Verified precisely before excluding: all 95 of 561 files matching "resume" case-insensitively use the exact `HeeGun-Eom-Resume-<Company>.md` convention, 0 exceptions — a precise pattern, not a broad heuristic. Re-running after the fix: the #1 result (BDR onboarding pair, 1.000) held, and 5-6 of the next 15 are genuine topical matches (interview prep/report pairs, related audits, GTM playbook pairs) | Live validation run, 2026-07-20 (before/after output in `meta/_changelog.md`) | A second, smaller template cluster (daily `APPLY-TODAY.md` job-queue files, numbered glossary pages) was observed post-fix and explicitly left unexcluded pending user decision — not silently patched |

## 11) Open questions

| ID | Question | Type (P/T/X) | Priority | Blocking? | Plan to resolve / next action | Status |
|---|---|---|---|---|---|---|
| Q1 | What triggers suggestion computation? | Product | P0 | Yes | Resolved by D1 | **Resolved** |
| Q2 | Chunk-level aggregation vs. new file-level embeddings? | Technical | P0 | Yes | Resolved by D2 | **Resolved** |
| Q3 | What similarity threshold for a suggestion? | Technical | P0 | Yes | Resolved by D3 | **Resolved** |
| Q4 | New persisted artifact or reuse existing index? | Technical | P0 | Yes | Resolved by D4 | **Resolved** |
| Q5 | New MCP tool vs. extending `reindex()`? | Technical | P0 | Yes | Resolved by D1 (folded in — same architectural choice) | **Resolved** |
| Q6 | How does "already linked" get determined, given no `[[...]]` parser exists yet? | Technical | P0 | Yes | A minimal `[[...]]` regex parser, mirroring `chunking.py`'s existing heading regex — no new dependency, no user-facing options to weigh. Implementer detail within D1's scope. | **Resolved** |
| Q7 | Does Claude write the confirmed link via `obsidian-mcp`'s `edit-note`, or does this stay suggestion-only forever? | Product | P2 | No | Noted in journey as crossing the server boundary; not blocking v1 design | Open (Future Work) |

## 12) Assumptions

| ID | Assumption | Confidence | Verification plan | Expiry | Status |
|---|---|---|---|---|---|
| A1 | HeeGun wants to build a linking habit going forward (the premise of choosing Option B at all) | HIGH (user explicitly chose this direction) | N/A — confirmed by user choice | N/A | Active |
| A2 | Reusing chunk embeddings (vs. new file-level embeddings) will produce acceptable suggestion quality | MEDIUM | Empirical — test against real vault data once built | Before finalization if possible, otherwise flagged as a Future Work trigger | Active |

## 13) In Scope (implement now)

- **Goal:** G1-G3 (§2) — surface reviewable `[[link]]` suggestions between semantically-close, currently-unlinked files, reusing existing infrastructure.
- **Non-goals:** NG1-NG4 (§3) — no auto-write, no real-time triggering, no file-level embeddings, no direct vault writes from this codebase.
- **Requirements with acceptance criteria:** §6.
- **Proposed solution:** §9 — new `linking.py` module + one new `suggest_links` MCP tool.
- **Owner(s)/DRI:** HeeGun Eom.
- **Next actions:** Implement `linking.py` (index-text-based `[[...]]` parser with fail-open resolution + file-centroid aggregation + threshold filter), register `suggest_links` tool in `server.py`, add `tests/test_linking.py` following the existing per-module test pattern.
- **Risks + mitigations:** §14.
- **What gets instrumented/measured:** Nothing formal (personal tool, same as base project) — success is HeeGun noticing and accepting useful suggestions.

**Resolution completeness gate check:**
- [x] All decisions affecting this item made (D1-D6, LOCKED/DIRECTED, no ASSUMED or INVESTIGATING remaining)
- [x] No 3rd-party dependency needed (reuses existing `sentence-transformers`/`numpy`/`fastmcp`)
- [x] Architectural viability validated — measured directly on the real index (not estimated): file-centroid all-pairs is 1.3MB, milliseconds
- [x] Integration feasibility confirmed — new module follows exact existing patterns (`Index.load`, matmul-based cosine similarity), no unknowns about whether it fits
- [x] Acceptance criteria verifiable — §6's table gives concrete, testable conditions
- [x] No dependency on an Out of Scope/Future Work item (Q7's write-path is explicitly noted as crossing into `obsidian-mcp` later, not required for this scope to function — suggestions are useful even if HeeGun inserts links manually)

## 14) Risks & mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Suggestions are noisy/low-quality at this vault's scale | Unknown — prior-art research found this genuinely underdocumented (`evidence/prior-art-pkm-link-suggestion.md`), not confirmed safe or confirmed risky | Medium — erodes trust in the feature, HeeGun stops using it | Suggest-only + reviewable (G3) is itself the primary mitigation; threshold tuning is a secondary lever | HeeGun |
| **Template/boilerplate similarity specifically:** many vault files are generated by structured skills (`technical-research`, spec-writing, career-ops) sharing scaffolding (headings like "Problem Statement," "Decision Log," boilerplate framing). MiniLM-style embeddings pick up shared surface structure, not just shared content — two unrelated reports built from the same template could score artificially high | Medium-High — this is a predictable mechanism for *this* corpus specifically, not a generic industry risk | Medium — false suggestions from shared scaffolding, not shared substance | If early suggestions look like matched-template noise rather than matched-content, that's this mechanism, not a broken threshold — first debugging hypothesis to check | HeeGun |
| File-centroid aggregation (D2) misses a niche shared idea buried in an otherwise-unrelated long file — the exact case chunk-pair max-pool was originally chosen to catch | Medium — a real, knowingly-accepted trade-off, not a surprise | Low-Medium — a missed suggestion is a silent gap (no error), not a wrong one | Chunk-level max-pool is documented in Future Work as the escalation path if this proves to matter in practice | HeeGun |

## 15) Future Work

### Explored
- **Chunk-pair max-pool aggregation** — the original D2 choice. Fully specified and was working code-path-viable, but superseded 2026-07-20 (audit + design-challenge) in favor of cheaper, more scale-robust file-centroid pooling. Revisit if centroid suggestions prove too coarse (e.g. miss connections HeeGun expected) — the implementation shape is already documented in this spec's decision history and `meta/audit-findings.md`/`meta/design-challenge.md`.
- **New file-level embeddings** (a fresh embedding pass, distinct from D2's centroid-pooling of existing embeddings) — investigated via prior art (Smart Connections ships both as a toggle). Not in scope (NG3) because it doubles embedding volume per reindex without evidence the cheaper pooling approaches (centroid or chunk-max-pool) are inadequate.
- **Auto-write of confirmed links via `obsidian-mcp`** — the natural next step after suggest-only proves out, crosses the reports-rag-mcp/obsidian-mcp server boundary. Not blocking v1.

### Identified
- **Real-time/automatic suggestion on file save** — would require reopening the base project's Decision #5 (on-demand-only rebuild). Not investigated deeply; noted as NG2.

### Noted
- **The original GraphRAG fusion idea (Option A)** — becomes newly viable *if* this link-suggestion tool succeeds in building real graph density over time. Not pursued now because the graph doesn't exist yet; the causality only runs one direction today.

## 16) Agent constraints

- **SCOPE:** One new file `src/reports_rag_mcp/linking.py` (index loading, link parsing/resolution, centroid aggregation, filtering). One new `@mcp.tool` registration in `src/reports_rag_mcp/server.py` (additive only — do not modify the existing `semantic_search`/`reindex` tool definitions). One new test file `tests/test_linking.py` following the existing per-module pattern (`test_chunking.py`/`test_indexer.py`/`test_search.py`).
- **EXCLUDE:** `chunking.py`, `indexer.py` — must remain untouched (D4/D5: no new persisted artifact, no reindex-time coupling). Any `.md` file under `~/.claude/reports` — read-only, this codebase never writes vault content (NG4, inherited LOCKED). The base project's `specs/reports-rag-mcp/SPEC.md` and its Decision Log — do not edit, only reference. The `obsidian-mcp` server/package — out of this codebase entirely, not modified.
- **STOP_IF:** Any need arises to persist a new artifact to `index_data/` or elsewhere (reopens D4 — LOCKED). Any need arises to have `linking.py` write to a `.md` file directly (violates NG4/D5's server-boundary design — must go through `obsidian-mcp`'s `edit-note` from the Claude/HeeGun side, never from this codebase). Real-usage testing shows file-centroid suggestions are consistently poor (reopens D2 — the Future Work escalation to chunk-pair max-pool is the documented next step, not a silent workaround). The 0.5 threshold (D3) needs frequent manual overriding to get useful results — that's a tuning signal, adjust the constant, but if adjusting it doesn't help, reopen D3/D2 rather than compensating elsewhere.
- **ASK_FIRST:** Before the first real `suggest_links()` run against the live vault (confirm suggestion quality looks reasonable on real data before treating the feature as done, matching the base project's own "ask first before first live index build" precedent). Before changing the locked threshold, aggregation strategy, or persistence decision from their spec'd defaults. Before any edit to `chunking.py`, `indexer.py`, or the existing MCP tool signatures.
