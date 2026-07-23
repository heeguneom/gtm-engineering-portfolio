# Design Challenge Findings

**Artifact:** /Users/genheegun/dev/reports-rag-mcp/specs/2026-07-20-link-suggestion-tool/SPEC.md
**Challenge date:** 2026-07-20
**Total findings:** 7 (2 High, 3 Medium, 2 Low)

---

## High Severity

### [H] Finding 1: File-centroid aggregation is a cheaper, simpler alternative to full chunk-pair max-pool, and wasn't evaluated against the chosen design

**Category:** DESIGN
**Source:** DC1
**Location:** §5 (journey step 2), §6 (aggregation requirements), §9 (System design), §10 D2, "Alternatives considered" (mean-pool row)
**Issue:** D2 chooses max-pool over an **all-pairs chunk-level similarity matrix**, then rolls the result up to file-pairs. The only alternative weighed against it in the Decision Log is **mean-pool over the same chunk-pair matrix** — a different reduction *after* the same expensive comparison. Neither option considers pre-aggregating each file's chunk embeddings into a single centroid vector (e.g. mean of that file's chunk vectors, computed in-memory from the already-loaded `vectors.npy` — no new embedding pass, no new model call) and then comparing **file-to-file** directly. That reframes the problem from an O(chunks²) comparison (~1,800² ≈ 3.24M pairs) to an O(files²) comparison (~561² ≈ 315K pairs — roughly 10x fewer), using the exact same underlying embeddings and zero new compute (satisfies G2's "reuse existing infrastructure" at least as well as the chosen design). It also mechanically removes two of the three Must-requirements added during the completeness re-sweep: "exclude same-file chunk pairs" becomes moot (you never form intra-file chunk pairs in the first place), and "deduplicate symmetric pairs" becomes a trivial `i < j` iteration guard instead of a post-hoc filter over a full matrix.

This is, in fact, the exact "chunk-level vs. file-level" fork the spec's own prior-art evidence calls out as "a live, unresolved fork industry-wide" (`evidence/prior-art-pkm-link-suggestion.md`, Smart Connections ships both as a toggle). But NG3 only evaluates and rejects *"file-level embeddings as a separate pass"* — i.e., re-**embedding** at file granularity with the model. It does not evaluate *deriving* file vectors from embeddings that already exist. These are materially different proposals with different costs: NG3's rejected option doubles embedding volume per reindex; the centroid alternative adds zero embedding cost and only touches the suggestion-time compute path.

**Current design:** "Chunk-pair aggregation via max-pool: file-pair score = highest-scoring chunk-pair between two files ... Reuses 100% existing embeddings at zero new cost; catches a specific shared idea buried in long/multi-topic files (the target 'aha moment')" (D2).

**Alternative:** Derive a per-file centroid (mean-pool) from each file's existing chunk vectors at call time, then compute the file×file similarity matrix directly (561×561 instead of 1,800×1,800), threshold and dedupe via `i < j` iteration.

**Trade-off:** The centroid alternative is cheaper, simpler to implement (no same-file exclusion logic, no post-hoc symmetric dedup, no per-file-pair max-reduction over matrix blocks), and stays at least as faithful to G2. What it loses is exactly what D2's own rationale says max-pool was chosen to catch: "a specific shared idea buried in long/multi-topic files." A centroid blurs a narrow shared topic across the rest of a file's content — for the spec's own "aha moment" example ("Claude surfaces a link between two reports HeeGun wrote months apart and forgot were related"), a whole-document-similarity signal would likely still catch topically-related reports, but would plausibly miss a niche shared idea buried inside two otherwise-unrelated documents.

**Status:** CHALLENGED
**Suggested resolution:** This is a genuine, evidence-grounded design fork that deserves explicit engagement, not necessarily a reversal. Options: (a) keep max-pool with the stated buried-idea rationale, but say so explicitly against the cheaper centroid alternative rather than only against mean-pool-of-the-same-matrix; (b) adopt centroid pooling as the v1 (cheaper, simpler, satisfies G1-G3) and treat max-pool-over-chunks as the Future Work escalation if centroid suggestions prove too coarse (mirrors this repo's own "start cheap, escalate on observed evidence" pattern, e.g. Decision #10's reversion in the base spec). Either is defensible — but the Decision Log currently reads as if max-pool vs. mean-pool were the only fork on the table, when a cheaper fork exists.

---

### [H] Finding 2: The "already linked" parser has no specified resolution step from wiki-link target text to the pipeline's file-path identifiers

**Category:** DESIGN
**Source:** DC2
**Location:** §6 (Must requirement: "Filter out pairs that are already linked"), §9 (System design, step 1)
**Issue:** The spec's own evidence shows real vault links are written as bare titles with no path or extension — `evidence/vault-link-density.md` cites `[[CAREER-OPS-HANDOFF]]` and `[[APPLICATIONS]]` as the two genuine cross-document links. But every other part of this codebase identifies files by **relative path from vault root**, forward-slash separated (`chunking.py`: `file_path: str  # path relative to the vault root`; `search.py`'s `metadata["file"]` uses this same convention). Nothing in §6 or §9 specifies how the parser resolves a bare wiki-link target like `CAREER-OPS-HANDOFF` to a specific `file_a`/`file_b` path such as `career-ops/CAREER-OPS-HANDOFF.md`. Obsidian itself solves this with basename-matching plus ambiguity handling when multiple files across different folders share a basename (a real possibility across a 561-file vault with subject-area subfolders). The spec's regex-parsing framing ("mirrors `chunking.py`'s existing heading regex") only addresses *syntax* extraction, not *resolution* to the identifiers the rest of the pipeline actually uses.

Getting this wrong has a direct, testable consequence against the spec's own Must requirement: if resolution silently fails (parser can't match `Target` text to any known `file_a`/`file_b`), an already-linked pair could be **re-suggested** — a direct violation of "A suggestion is never surfaced for a pair where `[[link]]` already exists between the two files." If resolution is too permissive (first-match-wins on an ambiguous basename), it could **wrongly suppress** a genuinely un-linked pair.

**Current design:** "requires new minimal `[[...]]` regex parser (Q6) — doesn't exist anywhere in the codebase today; mirrors `chunking.py`'s existing heading-regex pattern" (§6); Q6 status marked **Resolved** with "Implementer detail within D1's scope" (§11).

**Alternative:** N/A — this isn't a case for a different approach, but a genuine gap: the resolution/matching step needs its own explicit design (even a minimal one — e.g., "match by case-insensitive basename against all indexed file paths; if ambiguous, treat as unresolved and don't suppress the suggestion" is a defensible one-liner) rather than being folded silently into "implementer detail."

**Trade-off:** Specifying this now costs a few sentences in §6/§9. Leaving it unspecified risks silent violation of the one Must requirement whose entire purpose is correctness ("filter out pairs that are already linked") — discovered only when HeeGun notices a suggestion for a pair he already linked, or a real pair never surfaces and he never finds out why.

**Status:** CHALLENGED
**Suggested resolution:** Add a concrete resolution rule to §6/§9 before this is implemented: how bare/aliased targets map to `file_a`/`file_b` path identifiers, and what happens on ambiguous or unresolvable matches (recommend: fail open — don't suppress the suggestion — since a false "already linked" is a worse failure mode than an occasional stale-looking duplicate suggestion, consistent with this spec's own "fail loud" bar).

---

## Medium Severity

### [M] Finding 3: Parsing "already linked" from live disk files (rather than the already-loaded index) adds an unaccounted I/O pass and a freshness mismatch between the two signals the tool combines

**Category:** DESIGN
**Source:** DC1 / DC2 (crosses both — simpler alternative + stakeholder/consistency gap)
**Location:** §9 System design, step 1 ("parses `[[...]]` occurrences from each file's raw text")
**Issue:** `chunking.py`'s section-splitting preserves full line text (`"\n".join(lines)`), so a `[[link]]` written anywhere in a file's body survives verbatim into that file's chunk `text` field in `metadata.json` — the index the tool already loads in step 2. The spec's proposed design instead re-reads every file's raw text from disk independently (step 1), which is a second, unaccounted-for full-vault I/O pass (561 files) on every `suggest_links` call — not reflected in D4's napkin math or in the "no new persisted artifact... same order of magnitude as `search.py`" framing, which only accounts for the matmul cost. It also creates a genuine (if narrow) consistency question: the "already-linked" signal is always fresh (reads current disk state) while the similarity scores are frozen at last-`reindex()` time — meaning the tool combines two signals from two different points in time on every call. That may be an acceptable, even reasonable choice, but it's not stated as a deliberate trade-off anywhere in the spec.
**Current design:** Step 1 of §9's architecture reads raw files directly; step 2 separately loads the index.
**Alternative:** Parse `[[...]]` occurrences from the already-loaded index's chunk `text` field (grouped by `file`) instead of re-reading the vault from disk. Simpler (no new file-walk/read code path, one fewer failure mode — no permission errors, no race against concurrent vault edits), and keeps both signals sourced from the same snapshot.
**Trade-off:** The index-based approach has one edge case the disk-read approach doesn't: word-window splitting on section text >600 words (`_split_into_word_windows` in `chunking.py`) splits purely on whitespace, so a link containing a space in its display text (`[[Target|Display Name]]`) could in principle straddle two chunk windows at a boundary, corrupting the pattern in both fragments. This is rare (long section + unlucky boundary position) but real, and worth an explicit call-out either way.
**Status:** CHALLENGED
**Suggested resolution:** Decide explicitly whether "already linked" should reflect live-disk state or last-indexed state, and if live-disk is intentional (e.g., to correctly exclude a link HeeGun added by hand since the last reindex), say so and account for the added I/O cost in the performance claim. If index-based is acceptable, it's simpler and removes an entire code path.

---

### [M] Finding 4: Template/boilerplate similarity is a specific, foreseeable noise mechanism for this exact vault, and is only captured generically

**Category:** DESIGN
**Source:** DC2
**Location:** §14 Risks & mitigations ("Suggestions are noisy/low-quality at this vault's scale")
**Issue:** Many files in `~/.claude/reports` are generated by structured skills (`technical-research`, spec-writing, career-ops reports) that share consistent scaffolding — headings like "Problem Statement," "Situation/Complication/Resolution," "Decision Log," boilerplate framing language, etc. (this very spec is an instance of that pattern). Chunk-level cosine similarity over MiniLM embeddings is known to pick up shared surface structure/register, not just shared substantive content — two unrelated reports that both happen to be built from the same template could score artificially high on chunk similarity due to shared scaffolding language rather than a real conceptual connection. The existing Risks table names "noisy/low-quality" suggestions as a generic, undocumented-industry-wide risk, but doesn't name this specific, foreseeable mechanism for *this* corpus, which is more actionable (e.g., it suggests a concrete first debugging hypothesis if early suggestions look spurious, and might argue for a higher threshold or a stopword/boilerplate-aware preprocessing step later).
**Current design:** "Suggestions are noisy/low-quality at this vault's scale | Unknown — prior-art research found this genuinely underdocumented... not confirmed safe or confirmed risky."
**Alternative:** N/A — not proposing a different mechanism, proposing the risk be named specifically rather than only generically, since the mechanism is predictable from known facts about how this vault is populated.
**Trade-off:** Costs one sentence in §14. Doesn't change scope or design.
**Status:** CHALLENGED
**Suggested resolution:** Add the template-boilerplate confound as a named sub-risk with its own note ("if early suggestions look like matched-template noise rather than matched-content, that's the boilerplate-similarity mechanism, not a broken threshold").

---

### [M] Finding 5: "No new tool at all — use the existing `semantic_search` tool via Claude's own orchestration" wasn't evaluated as an alternative to building `suggest_links`

**Category:** DESIGN
**Source:** DC1
**Location:** §9 "Alternatives considered," §10 D1
**Issue:** The Decision Log's D1 alternatives ("Automatic/passive suggestion," "Reindex-coupled batch computation") both assume a *new dedicated capability* is being built — the fork evaluated is "what shape should the new tool take," not "does a new tool need to exist at all." A genuinely zero-new-code alternative exists: Claude already has `semantic_search`. For any file HeeGun or Claude is actively working on, Claude could excerpt that file's content and call `semantic_search` with it as a query, inspect the returned chunks from other files, and judge candidate links itself — no `linking.py`, no new MCP tool, no new tests, no `[[...]]` parser at all (Claude can eyeball whether a link already exists by reading the target file). This achieves a meaningful slice of G1 with zero implementation cost.
**Current design:** D1 locks in a new dedicated `suggest_links` MCP tool as a batch, corpus-wide sweep.
**Alternative:** No new tool; rely on Claude invoking `semantic_search` per-file as an ad hoc orchestration pattern when relevant.
**Trade-off:** The ad hoc approach can't deliver G1's implied capability — "surface candidate `[[link]]` pairs" reads as a systematic, corpus-wide sweep, not an incidental check that only fires when Claude happens to be looking at a specific file. Reproducing full corpus coverage via repeated single-file `semantic_search` calls would mean up to 561 sequential tool invocations, no principled threshold/dedup/same-file handling, and would be expensive in tool-call volume and Claude's context budget — the ad hoc version is not a comprehensive substitute, just a cheaper partial one.
**Status:** CHALLENGED
**Suggested resolution:** The current design likely still wins this comparison (G1 reads as requiring systematic coverage, which the ad hoc path can't deliver economically), but the Decision Log doesn't currently show this "build nothing new" option was considered and rejected — worth a one-line addition to "Alternatives considered" for completeness, since it's the simplest possible alternative to any new-code proposal.

---

## Low Severity

### [L] Finding 6: Journey ambiguity on whether Claude can write a link without per-suggestion HeeGun confirmation

**Category:** DESIGN
**Source:** DC2
**Location:** §5 User journeys, P1 happy path steps 3-4
**Issue:** Step 3 says "Claude presents suggestions to HeeGun, **or acts on them directly if instructed**"; step 4 says "HeeGun confirms; Claude uses `obsidian-mcp`'s `edit-note`..." It's not clear from the text whether "acts on them directly if instructed" means Claude can skip per-suggestion confirmation given some standing instruction from HeeGun (in which case G3's "reviewable... no silent auto-linking" framing has an unstated escape hatch), or whether "instructed" just means HeeGun says "yes, add that one" in the moment (in which case step 3 and step 4 are describing the same thing twice, redundantly). NG1 ("no auto-inserting... without human/**Claude** review") suggests Claude's own review alone might be considered sufficient without HeeGun in the loop each time — which is a materially different guarantee than what G3's wording implies to a reader.
**Current design:** As quoted above.
**Alternative:** Clarify explicitly: does every write require HeeGun's per-instance confirmation, or can a standing instruction let Claude write without asking each time?
**Trade-off:** Low cost to clarify (a sentence), but matters because G3 is stated as a trust-building safety property of this whole feature, and the journey text as written doesn't unambiguously deliver on it.
**Status:** CHALLENGED
**Suggested resolution:** Pick one and state it plainly in §5 and §6 (recommend: every write requires HeeGun's explicit response to that specific suggestion, matching NG1's "human/Claude review" language toward the stricter reading).

---

### [L] Finding 7: The Complication's growth-urgency clause is asserted, not evidenced, and isn't load-bearing for the Resolution

**Category:** DESIGN
**Source:** DC3
**Location:** §1 Problem statement, Complication
**Issue:** "the vault's growing size (561 files, ~1.04M words, growing via the `technical-research` skill) means the lack of structure will only get more costly as it scales" is stated without any supporting analysis of what "cost" means here or how it scales (no query-quality-vs-corpus-size data, no measurement of navigation friction). Testing DC3's removal heuristic: if this clause were deleted from the Complication entirely, the Resolution ("use existing embeddings to suggest links, build a real graph over time") would still be fully justified by the core finding alone — 559/561 files have zero real links, and prior art strongly converges on suggest-then-review as the right pattern regardless of vault growth rate. The growth clause reads as an added urgency flourish rather than a load-bearing part of the argument.
**Current design:** As quoted above.
**Alternative:** N/A — not proposing a different resolution, just noting the framing doesn't need this clause to hold.
**Trade-off:** None — doesn't change scope, doesn't change the recommendation. Purely a framing-precision note.
**Status:** CHALLENGED
**Suggested resolution:** Either drop the clause or replace it with the concrete fact that's actually load-bearing (the base spec's own confirmed ~a-few-reports/week growth rate, `specs/reports-rag-mcp/SPEC.md` §12), rather than an unquantified "more costly as it scales" assertion.

---

## Confirmed Design Choices (summary)

**DC1 (simpler alternative):**
- D1 (new dedicated on-demand `suggest_links` tool, not coupled to `reindex()`) holds up — matches the base spec's own locked on-demand philosophy and the strongest prior-art pattern (explicit-invoke-then-review). No simpler on-demand-vs-coupled fork was missed.
- D4 (in-memory computation, no new persisted artifact) holds up regardless of which pooling strategy wins (Finding 1) — the napkin math correctly shows either the chunk-matrix or the (cheaper) file-centroid version stays well within sub-second budget at current scale.
- The rejection of "automatic/passive" (live-note-view-triggered) suggestion holds — there's genuinely no editor/view-state signal exposed to an MCP server in this Claude Code context, independently verified against how `semantic_search`/`reindex` are invoked today.

**DC2 (stakeholder gap):**
- No silent-vault-write path: NG4 (inherited, LOCKED) and the explicit "never write to stdout" / "no silent auto-write" Must requirements are correctly carried through consistently in §6, §9, and the journey (modulo Finding 6's wording ambiguity).
- Empty-result handling (no forced weak matches below threshold) correctly mirrors the base project's existing filter-don't-force pattern (Decision #8) rather than introducing new behavior.
- Index-missing failure mode correctly reuses `semantic_search`'s existing clear-error pattern rather than inventing a new one.

**DC3 (framing validity):**
- The core Complication claim — "almost no real link structure exists" — is directly, freshly measured (`grep -rohE` across all 561 files, `evidence/vault-link-density.md`), not asserted. This is the strongest-evidenced part of the spec and fully supports the pivot from "GraphRAG fusion" to "suggest-only" framed in the Resolution.
- The Resolution's reliance on "suggest, review, human confirms" as the dominant, safest pattern is well-triangulated against real prior art (4 tools surveyed, convergent rationale), not a post-hoc justification for a pre-chosen design.
