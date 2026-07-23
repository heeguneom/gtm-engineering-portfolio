# Audit Findings

**Artifact:** /Users/genheegun/dev/reports-rag-mcp/specs/2026-07-20-link-suggestion-tool/SPEC.md
**Audit date:** 2026-07-20
**Total findings:** 3 (2 High, 0 Medium, 1 Low)

---

## High Severity

### [H] Finding 1: D4's napkin math is built on a stale chunk-count figure — real index is ~6.4x larger than assumed

**Category:** FACTUAL
**Source:** T1 (own codebase / on-disk index artifact)
**Location:** §6 Non-functional requirements ("Performance: Sub-second per call at current scale (~1,800 chunks)"); §5 Interaction state matrix ("Loading: N/A (sub-second per napkin math, D4)"); §10 Decision D4; §13 Resolution completeness gate ("Architectural viability validated — napkin math (D4) confirms in-memory computation is fast enough at current scale")

**Issue:** The spec repeatedly treats "~1,800 chunks" as the current corpus scale and uses it to justify D4 (no new persisted artifact — compute the all-pairs chunk-similarity matrix in memory at call time). This figure is carried over from the *base* project's spec (`specs/reports-rag-mcp/SPEC.md`, e.g. NG4: "corpus grows an order of magnitude beyond current scale (~1,800 chunks today)") without re-checking it against the actual current index — even though this spec's own Baseline commit (`0962921`) is the exact commit that produced the on-disk index.

**Current text:** "Napkin math: ~1,800 chunks → all-pairs cosine similarity matrix ≈ 1,800×1,800×4 bytes ≈ 13MB, one numpy matmul, same order of magnitude as what `search.py` already does per query — sub-second, no performance case for persistence" (D4, §10); "Performance: Sub-second per call at current scale (~1,800 chunks)" (§6).

**Evidence:** Read directly from the live index at `/Users/genheegun/dev/reports-rag-mcp/index_data/`:
- `vectors.npy` header: `{'descr': '<f4', 'fortran_order': False, 'shape': (11536, 384)}` — **11,536 chunks**, not ~1,800.
- `metadata.json` independently confirms 11,536 entries (`grep -o '"file":' metadata.json | wc -l` → 11536).
- Both files are dated 2026-07-16 17:23, built from commit `0962921` — the same commit this spec cites as its own Baseline commit (`git log -1 --format="%H %ai" 0962921` → `2026-07-16 15:41:02`, i.e. the index was built ~40 minutes after that exact commit). This is not old/orphaned data; it is the current index for the current codebase state this spec claims to be scoped against.
- Recomputed at actual scale: an all-pairs matrix is 11,536×11,536×4 bytes ≈ **532MB**, not ≈13MB (a ~41x understatement, since matrix size scales with n²).
- Notably, the *base* spec's own STOP_IF trigger (§16 of `specs/reports-rag-mcp/SPEC.md`) is: "Actual corpus size proves to be an order of magnitude beyond current napkin math (~1,800 chunks) — reopen NG4." At 11,536 chunks (~6.4x), the corpus is already approaching that self-defined reopen threshold — a fact this spec doesn't surface anywhere, despite building new all-pairs computation directly on top of the same assumption.

**Status:** STALE

**Suggested resolution:** Re-run the napkin math in D4 against the actual current chunk count (11,536, or re-measure at implementation time since the vault continues to grow). Confirm whether ~532MB of intermediate matrix memory and the correspondingly larger matmul are still acceptable for "no new persisted artifact, sub-second." If not, D4 may need to be reopened — e.g. blocking/tiling the computation, pre-filtering by file before going to full chunk-level pairwise comparison, or revisiting whether in-memory-only is still the right call at this scale. This is a decision-implicating factual finding, not a wording fix: it undermines the evidence basis of a LOCKED decision (D4) and a checked-off resolution-completeness-gate item (§13).

---

### [H] Finding 2: D4's complexity comparison to `search.py` is not "the same order of magnitude" — it's a different asymptotic class

**Category:** COHERENCE
**Source:** L4 (evidence-synthesis fidelity)
**Location:** §10 Decision D4

**Issue:** Independent of Finding 1's stale-number issue, the qualitative claim itself doesn't hold at any chunk count. `search.py`'s per-query cost (verified by direct read of `search.py`) is a **matrix-vector** multiply: one query embedding (384-dim) against n stored chunk vectors → O(n·d) work. The proposed `suggest_links` computation described in §9 ("computes an all-pairs chunk-similarity matrix via the same normalize+matmul pattern as `Index.search()`") is a **matrix-matrix** multiply: all n chunks against all n chunks → O(n²·d) work. These are different complexity classes, not "the same order of magnitude" — at n=1,800 the all-pairs step is already ~1,800x more multiply-adds than a single `semantic_search` query; at the real n=11,536 (Finding 1) it's ~11,536x more.

**Current text:** "...one numpy matmul, same order of magnitude as what `search.py` already does per query — sub-second, no performance case for persistence" (D4, §10).

**Evidence:** `search.py` (`Index.search`): `scores = vector_norms @ query_norm` — a single (n, d) @ (d,) operation. §9's proposed `linking.py` design: "computes an all-pairs chunk-similarity matrix via the same normalize+matmul pattern" — a (n, d) @ (d, n) operation producing an (n, n) matrix. The former is linear in n; the latter is quadratic in n.

**Status:** INCOHERENT

**Suggested resolution:** Correct the rationale in D4 to acknowledge the actual complexity relationship (quadratic all-pairs step vs. linear per-query search), and re-derive the "sub-second" claim from that basis combined with the corrected chunk count from Finding 1, rather than asserting equivalence to `search.py`'s query cost. The conclusion ("in-memory, no persistence needed") may still hold, but it needs to be re-earned with the corrected math rather than resting on a false equivalence.

---

## Low Severity

### [L] Finding 3: "Never write to stdout" requirement overstates `server.py`'s current logging behavior

**Category:** FACTUAL
**Source:** T1 (own codebase)
**Location:** §6 Functional requirements, "Never write to stdout" row

**Issue:** The requirement's acceptance criteria states new logging should go "to stderr, same as `indexer.py`/`server.py` today." `indexer.py` does configure an explicit stderr `logging.StreamHandler` (verified by direct read). `server.py`, as it exists today, has no `logging` import or logger configuration at all — it satisfies "never writes to stdout" simply by not printing anything, not by actively logging to stderr the way `indexer.py` does. The functional requirement itself is fine (new code should log to stderr), but the stated precedent slightly overclaims what `server.py` currently does.

**Current text:** "All logging in any new module goes to stderr, same as `indexer.py`/`server.py` today."

**Evidence:** `server.py` (full file read) contains no `import logging`, no logger, and no log calls — only the two `@mcp.tool` functions and `main()`.

**Status:** INCOHERENT (minor — prose overstates current-state evidence, doesn't affect the requirement's validity)

**Suggested resolution:** Minor wording fix — e.g. "same as `indexer.py` today; `server.py` currently has no logging but must follow the same stderr-only convention if any is added."

---

## Confirmed Claims (summary)

**T1 (own codebase), high coverage:**
- `chunking.py`: heading-only regex (`^(#{1,6})\s+(.*)$`), 600-word cap, no `[[...]]` or frontmatter parsing — confirmed.
- `indexer.py`: local `all-MiniLM-L6-v2` via `sentence-transformers`, flat `metadata.json`/`vectors.npy`, full rebuild every call, atomic `.tmp` + `Path.replace()` write, stderr-only logging — confirmed.
- `search.py`: `SIMILARITY_THRESHOLD = 0.3`, normalize+matmul cosine similarity, results below threshold filtered — confirmed.
- `server.py`: two `@mcp.tool` functions (`semantic_search`, `reindex`), env-var paths with home-relative fallback — confirmed.
- Base spec decision citations (Decisions 1, 2, 5, 6, 8, 10 and NG1/NG3/NG4) — all accurately quoted/summarized against `specs/reports-rag-mcp/SPEC.md`.
- Baseline commit `0962921` matches actual repo HEAD (`git log`) — confirmed.

**Direct measurement against the vault (`~/.claude/reports`):**
- 561 `.md` files — confirmed exact match.
- ~1.04M words (1,043,129 measured) — confirmed exact match.
- 4 of 561 files contain any `[[...]]` syntax, 20 total occurrences, exactly 2 genuine cross-document links (`[[APPLICATIONS]]`, `[[CAREER-OPS-HANDOFF]]`) — confirmed exact match via independent `grep -rohE '\[\[[^]]+\]\]'` re-run.

**T2/T1 (obsidian-mcp installed package):**
- `obsidian-mcp` README (read directly from the installed npm package) lists exactly the 12 tools cited, with no backlinks/graph tool — confirmed.

**T5 (external prior art, web-verified):**
- Semantic Backlinks (`brightwav3/semantic-backlinks`) default similarity threshold is 0.35 cosine — confirmed via web search of the project's own docs/GitHub.
- `joybro/obsidian-similar-notes` defaults to `all-MiniLM-L6-v2` — confirmed via web search.
- Smart Connections uses local `bge-micro-v2` (`TaylorAI/bge-micro-v2`) by default, no API key — confirmed via web search.

## Unverifiable Claims

- **Semantic Auto-Linker's "review modal with live graph-change preview before writing"** (evidence/prior-art-pkm-link-suggestion.md) — evidence file itself already flags this as MEDIUM confidence / single-channel. Not independently re-verified here (would require deep GitHub repo inspection beyond a search-engine check); no reason to doubt it, but not confirmed to a higher bar either.
- **Karpathy's "LLM Wiki" pattern** — evidence file already flags MEDIUM confidence / single HN thread + gist. Not re-verified.
- **A1 ("HeeGun wants to build a linking habit going forward")** — correctly left as a user-intent assumption (HIGH confidence, "confirmed by user choice"), not something to fact-check against an external source.
- **"the vault's growing size... growing via the `technical-research` skill"** (§1 problem statement) — plausible and consistent with the observed 561-file/1.04M-word corpus, but growth *rate* and its attribution specifically to that skill wasn't independently measured (e.g. no commit-history/timestamp analysis of the vault was run). Doesn't affect the spec's conclusions either way.
