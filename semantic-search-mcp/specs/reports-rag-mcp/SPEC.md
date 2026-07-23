# Semantic Search MCP Server for ~/.claude/reports — Spec

**Status:** Approved
**Owner(s):** HeeGun Eom
**Last updated:** 2026-07-16
**Baseline commit:** N/A (no git repo — personal machine project)
**Links:**
- Curriculum this satisfies: `~/.claude/reports/gtm-growth-engineering-technical-curriculum/REPORT.md` (items #10 RAG, #12 MCP)
- Evidence: `./evidence/`

---

## 1) Problem statement

**Situation:** HeeGun maintains a personal knowledge vault (`~/.claude/reports/`, 556 markdown files, ~1.04M words) that grows automatically via the `technical-research` skill. It's connected to Claude Code via the `obsidian-mcp` server, which supports keyword/filename/tag search only.

**Complication:** In practice, HeeGun regularly has to manually locate and paste specific report files into context before Claude can work on a problem, and has to remind Claude of prior formalized context (a report) that already exists but wasn't surfaced. Keyword search doesn't bridge this — it only finds content that shares exact terms with the query, not content that's conceptually related but differently worded. This is a confirmed, experienced friction (not hypothetical), and it's also the natural next hands-on project in HeeGun's technical curriculum (RAG + MCP server-building, items #10 and #12).

**Resolution:** Build a semantic search layer (RAG) over the vault, exposed as a custom local MCP tool, so Claude can retrieve conceptually relevant chunks by meaning rather than exact keyword — reducing how often HeeGun has to manually supply context Claude should already be able to find.

## 2) Goals
- G1: Claude (this session and future ones) can semantically search across all 556+ reports and get back relevant chunks with source attribution, without HeeGun manually locating/pasting files.
- G2: The whole system runs locally, using only free/already-available tooling — no new paid API or service subscription.
- G3: HeeGun builds and understands every core piece himself (chunking, embedding, similarity search, MCP server) — this is a learning project, not just an integration.
- G4: The index stays reasonably current as new reports are added (vault grows via the `technical-research` skill on an ongoing basis).

## 3) Non-goals
- **[NOT NOW]** NG1: Real-time/incremental re-indexing on file save, AND mtime-based skip-unchanged-files, AND deleted/renamed-file reconciliation — bundled together as one future package, not built separately. — Revisit if: full-rebuild time becomes annoying *in practice* (napkin math says it shouldn't at current scale — see `evidence/corpus-scale-napkin-math.md`). v1 uses plain full-rebuild-on-demand (Decision 5), which has no orphan-entry problem since it reconstructs the index from scratch each time.
- **[NOT NOW]** NG2: Replacing `obsidian-mcp`'s keyword/filename search or its write tools (create-note, edit-note, tags). — Revisit if: semantic search proves to fully subsume keyword search in practice (unlikely — exact-term lookups like company names are keyword search's strength).
- **[NEVER]** NG3: Any paid embedding API or hosted vector database — explicit user constraint ("what is possible without having to pay for any additional services").
- **[NOT UNLESS]** NG4: A dedicated vector database (Chroma/LanceDB/sqlite-vec). — Only if: corpus grows an order of magnitude beyond current scale (~1,800 chunks today; napkin math in `evidence/corpus-scale-napkin-math.md` shows brute-force search stays sub-100ms well past that).

## 4) Personas / consumers
- P1: HeeGun, via Claude Code sessions, calling the tool through MCP during normal work.
- P2 (secondary, same shape): Any other MCP client HeeGun configures against the same server (e.g. Claude Desktop), if ever.

## 5) User journeys

**P1 happy path:**
1. HeeGun starts a task that touches a domain he's likely researched before (e.g. "let's revisit the BDR onboarding comp structure").
2. Instead of HeeGun locating and pasting the relevant report, Claude calls `semantic_search("BDR onboarding comp structure")`.
3. Tool returns top-k ranked chunks with source file + section + snippet.
4. Claude reads the most relevant chunk(s) inline, or calls the existing `obsidian-mcp` `read-note` for the full file if more context is needed.
5. Work proceeds without HeeGun re-explaining prior formalized context.

**Failure / recovery path:**
- Index is stale (new reports added since last rebuild) → results miss recent reports. Recovery: HeeGun or Claude runs the reindex tool/command; no data loss, just staleness.
- Query has no good semantic match (topic genuinely not researched before) → tool returns low-relevance results; Claude/HeeGun should recognize low similarity scores and fall back to keyword search or acknowledge the gap, not present a bad match as authoritative.

**"Aha moment":** Claude surfaces a relevant report HeeGun forgot existed, phrased in different words than the query — the first time this happens is the validation that G1 is met.

**Debug experience:** If results seem wrong, HeeGun can inspect the index file directly (it's a flat local file, not a black-box service) and re-run the rebuild script to see raw chunking/embedding output.

### Interaction state matrix

| Feature / Surface | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| `semantic_search` MCP tool | N/A (sub-second, no async loading state needed) | No chunks in index yet (never indexed) → clear error message, not silent empty list | Index file missing/corrupt → clear error directing to run rebuild | Ranked chunks returned with scores | Index stale (some reports post-date last build) → results still returned, no explicit "stale" signal in v1 (see Open Questions) |
| Reindex (CLI + MCP tool) | Full rebuild, ~2 min at current scale (Decision 5); should print file count as it runs (to stderr — see §13 stdout-corruption risk) | N/A | A single file fails to parse/embed → skip + log (to stderr), don't abort whole rebuild | New index written from scratch, old one replaced atomically — inherently excludes deleted/renamed files, no orphan entries possible | N/A |

## 6) Requirements

### Functional requirements
| Priority | Requirement | Acceptance criteria | Notes |
|---|---|---|---|
| Must | Chunk all markdown files in `~/.claude/reports/` by heading section | Every `.md` file produces ≥1 chunk; long sections split further at a word-count cap | See Decision: Chunking strategy |
| Must | Embed all chunks locally, no API calls | Full corpus embeds with zero network calls to a paid provider | See Decision: Embedding model |
| Must | Persist the index to a local file that survives process restarts | Killing/restarting the MCP server does not require re-embedding | See Decision: Storage |
| Must | Expose a `semantic_search(query, top_k)` MCP tool | Given a natural-language query, returns top_k chunks ranked by similarity, each with source file path, section heading, snippet text, and score | Core deliverable |
| Must | Provide a way to rebuild the index after new reports are added | A CLI command (and/or MCP tool) that re-scans the vault and rewrites the index | Full rebuild acceptable per napkin math (NG1) |
| Must | Expose `reindex` as an MCP tool, callable by Claude mid-session, in addition to a CLI entry point | Claude can call `reindex()` mid-session; CLI `python reindex.py` also works standalone | Decision 7 (rationale revised — see Decision Log) |
| Must | Filter `semantic_search` results below a similarity threshold (default ~0.3, tunable) | Query with no good match in the vault returns an explicit "no relevant reports found" rather than weak/irrelevant top-k | Decision 8 |

### Non-functional requirements
- Performance: Query latency sub-second at current and 10x corpus scale (see napkin math).
- Reliability: A corrupted/missing index should fail loudly with a clear message, never silently return empty/wrong results.
- Security/privacy: No report content or query text leaves the local machine (hard requirement given sensitive personal/career data in some reports).
- Operability: N/A at this scale (single user, local process, no fleet to monitor) — rebuild should print basic progress (file count processed) to stderr for debuggability (never stdout — see §13).
- Cost: $0 — no paid API, no paid service, at any usage volume.

## 7) Success metrics & instrumentation
- Metric 1: Reduction in "let me paste this report" moments during Claude sessions.
  - Baseline: Not formally tracked (self-reported friction).
  - Target: Qualitative — HeeGun notices Claude finding relevant prior work unprompted.
  - Instrumentation notes: No formal telemetry planned; this is a personal tool, success is judged by HeeGun's own experience of it, not a dashboard.
- What we'll log: reindex run timestamp + file count, for debugging staleness only.

## 8) Current state (how it works today)

- `obsidian-mcp` server (npx-based, `~/.claude.json`) points at `~/.claude/reports/`, exposes `search-vault` (content/filename/tag keyword search), `read-note`, `create-note`, `edit-note`, `move-note`, `delete-note`, tag management.
- No semantic search exists. No frontmatter/tags on most of the 556 files (folder structure is the only organization).
- Vault: 556 `.md` files, ~1.04M words total (`evidence/corpus-scale-napkin-math.md`).
- Local environment: `uv` + Python 3.12 available at `~/.local/bin/`; default `python3` on PATH resolves to an unusable Python 3.5. Homebrew itself works fine — no Python is currently brew-installed, `uv` is simply the better-suited tool here (`evidence/local-environment.md`).

## 9) Proposed solution (vertical slice)

### User experience / surfaces
- No UI — this is entirely an MCP tool surface consumed by Claude.
- CLI: a rebuild/reindex script HeeGun can run manually from the terminal.
- MCP: new server registered in `~/.claude.json` alongside the existing `obsidian` entry.

### System design (decisions locked — see §10 Decision Log)
- **Architecture overview:** A Python project (managed via `uv`) with two pieces: (1) an indexer script that walks the vault, chunks each file by heading, embeds chunks with a local sentence-transformer model, and writes a flat local index file; (2) an MCP server (FastMCP-based) that loads the index at startup and exposes `semantic_search` and `reindex` as tools.
- **Data model:** Each index entry = `{file_path, heading, chunk_text, embedding_vector}`. Stored as a single local file — JSON metadata + `.npy` vector array (Decision #2, LOCKED).
- **Transport:** stdio MCP server, matching the existing `obsidian` server's pattern in `~/.claude.json`.
- **Auth/permissions:** None needed — local process, local file access, single user.
- **Enforcement point(s):** N/A.
- **Observability:** Basic stdout logging during reindex (file count, skipped files); no other instrumentation planned given scale.

### Alternatives considered
- **Vector database (Chroma/LanceDB/sqlite-vec)** — rejected for v1: solves a scale problem this corpus (~1,800 chunks) doesn't have; adds a dependency and a format to learn without adding capability at this size. Revisit per NG4.
- **RAG framework (LangChain/LlamaIndex)** — resolved: hand-rolled (Decisions #1, #4, #9). The "understand every part" goal (G3) plus the "no paid services" constraint both pushed toward the simplest stack. Note: Decision #9 (FastMCP for the MCP transport layer) is a deliberate scope boundary within G3, not an oversight — the RAG-specific mechanics that are the actual point of the learning project (chunking, embedding, similarity search) remain fully hand-rolled; only the MCP protocol plumbing uses a framework, which materially reduces boilerplate for a single-user, two-tool server.
- **API-based embeddings (OpenAI/Voyage)** — rejected: violates the "no paid services" constraint (NG3) and the privacy requirement (sensitive personal/career data in some reports should not leave the machine).

---

## 10) Decision Log

| # | Decision | Status | Confidence | Notes |
|---|---|---|---|---|
| 1 | Embeddings: `all-MiniLM-L6-v2` via local `sentence-transformers` (no API) | LOCKED | HIGH | User-confirmed. Free, local, ~80MB download, CPU-fast, proven for this retrieval style. |
| 2 | Vector store: flat local file (JSON metadata + `.npy` vector array), no vector DB | LOCKED | HIGH | User-confirmed. Evidence-backed by napkin math — ~1,800 chunks doesn't need a dedicated vector DB. |
| 3 | Implementation language: Python via `uv` | LOCKED | HIGH | Matches sentence-transformers' ecosystem and FastMCP; avoids the broken system Python by using `uv`. Confirmed installable — `evidence/fastmcp-viability.md`. |
| 4 | Chunking: by markdown heading section, ~600-word cap per chunk, fixed-size fallback for headless files | LOCKED | HIGH | User-confirmed. |
| 5 | Re-indexing trigger: on-demand rebuild (not live file-watching) | LOCKED | HIGH | Napkin math shows full rebuild is sub-2-minutes at current scale. |
| 6 | Coexist with `obsidian-mcp`, do not replace | LOCKED | HIGH | Keyword/filename search and all write tools (create/edit/move/delete/tags) stay on `obsidian-mcp`; new server is additive. |
| 7 | `reindex` exposed as an MCP tool (Claude-callable), in addition to CLI | LOCKED | HIGH | User-confirmed. **Revised rationale post-audit:** delivers "Claude can refresh the index when asked, without HeeGun needing a separate terminal step" — not autonomous staleness detection (see Finding G resolution below; `semantic_search` carries no staleness signal, so framing this as "notices staleness without being asked" overclaimed the design). |
| 8 | Low-similarity results are filtered below a threshold, not always returned | LOCKED | HIGH | User-confirmed. Default threshold ~0.3 cosine similarity (MEDIUM confidence on the exact number — standard starting point for MiniLM-style embeddings, tune empirically after first real usage). |
| 9 | MCP server framework: FastMCP (not the raw `mcp` SDK) | LOCKED | HIGH | `uv add fastmcp`, stdio transport by default — matches the existing `obsidian` entry's transport shape. `evidence/fastmcp-viability.md`. |
| 10 | ~~Reindex is mtime-aware: skip embedding unchanged files~~ — **SUPERSEDED, reverted to plain full-rebuild** | SUPERSEDED | — | **Reopened via design-challenge audit (2026-07-16) and reverted.** Original promotion was based on speculative reasoning ("could in principle be triggered more often than useful"), not observed annoyance — this violated NG1's own explicit deferral trigger ("revisit if full-rebuild time becomes annoying *in practice*"). Reverting also resolves the deleted/renamed-file gap (Finding B) for free: a full rebuild-from-scratch has no orphan-entry problem, since it only ever contains files currently on disk. If reindex frequency/latency proves annoying in real use, incremental skip + deletion-reconciliation should be built together, with real evidence, per NG1. |

---

## 11) Open Questions

All P0 open questions are resolved (see Decision Log #1-10). Remaining P2 items resolved autonomously (low-stakes, no established convention to conflict with — checked, no existing `~/dev`, `~/projects`, `~/code` directory on this machine):

| # | Question | Type | Priority | Status |
|---|---|---|---|---|
| 7 | Project directory location | Technical | P2 | Resolved: `~/dev/reports-rag-mcp` (new convention, first project of its kind on this machine) |
| 8 | `semantic_search` tool parameter schema | Technical | P2 | Resolved: `semantic_search(query: str, top_k: int = 5) -> list[{file, heading, snippet, score}]`; `reindex() -> {files_processed, files_skipped, chunks_total, duration_s}` |

---

## 12) Assumptions
- Corpus growth rate stays roughly similar (a few reports/week via the research skill) — if it grew 10-100x, napkin math conclusions (no vector DB needed, full rebuild fine) would need revisiting. Confidence: HIGH given current trajectory.
- HeeGun will run the reindex step manually often enough to keep the index reasonably fresh, OR we expose it as an MCP-triggerable tool (Decision #7).

## 13) Risks / Unknowns
- **Risk:** Local embedding model quality is lower than a paid API (e.g. OpenAI's `text-embedding-3`) — retrieval may be less precise. Mitigation: modern small local models (MiniLM/BGE-small) are good enough for this use case's scale and query style; can revisit if retrieval quality proves inadequate in practice.
- **Unknown:** How well heading-based chunking handles the more unusual file structures in the vault (e.g. very long files with deep nesting, or files with no headings at all like `2026-07-15.md`). Will surface during implementation, not fully knowable upfront.
- **Risk (implementation gotcha, confirmed):** stdio-mode MCP servers must never write to stdout — any `print()`-style debug/progress output during `reindex` will corrupt the JSON-RPC stream and break the server. Mitigation: all logging must go to stderr. `evidence/fastmcp-viability.md`.
- **Risk (accepted, not mitigated — per NG1):** `reindex` being Claude-callable (Decision 7) means each call is a full rebuild, ~2 minutes at current scale. This is an accepted trade-off for v1 simplicity, not engineered around speculatively. If this proves annoying in actual use, that's the NG1 trigger firing — build incremental skip + deletion-reconciliation together then, with real evidence of frequency/annoyance.
- **Unknown:** Default similarity threshold (~0.3) is a reasonable starting point but not empirically tuned against this specific corpus yet — may need adjustment after real usage (Decision 8).

## 14) Future Work
- **[Explored]** Incremental/mtime-based reindexing + deleted/renamed-file reconciliation — investigated and briefly promoted to in-scope (Decision 10), then reverted after design-challenge audit surfaced that the promotion was speculative and violated NG1's own evidence-based trigger. Deferred as one bundled package per NG1: build both together if/when full-rebuild time is actually observed to be annoying, not before.
- **[Explored]** Vector database migration — clear trigger condition (10x+ corpus growth) and clear replacement path (same chunk/metadata schema, swap storage/query layer).
- **[Identified]** Frontmatter/tagging convention for new reports, to enable hybrid keyword+semantic filtering (e.g. "semantic search within `tags: bdr`"). Not investigated deeply this pass.
- **[Noted]** Auto-surfacing behavior (Claude proactively checking semantic search before starting relevant work, without being asked) — this is a usage-pattern/instruction concern (e.g. a CLAUDE.md rule) more than a system architecture concern; the MCP tool built here is the prerequisite either way.

---

## 15) Constraints (Agent Constraints)

- **SCOPE:** New project directory `~/dev/reports-rag-mcp/` (indexer script, MCP server, index file, `pyproject.toml`/`uv` files). One addition to `~/.claude.json`: a new MCP server entry registering this project, added alongside existing entries.
- **EXCLUDE:** `~/.claude/reports/` vault content — read-only access for chunking/embedding; never write, edit, move, or delete report files (that's `obsidian-mcp`'s job, per Decision 6). The existing `obsidian` entry in `~/.claude.json` and any other MCP server entries. The `technical-research` skill or any other skill.
- **STOP_IF:** Any need arises to add a paid API key or external service credential (hard violation of NG3). Any need arises to modify or remove an existing `~/.claude.json` entry other than adding the new one. `sentence-transformers` or `fastmcp` fail to install cleanly via `uv` (would mean Decision 1/3/9's viability assumption was wrong — reopen, don't route around). Actual corpus size proves to be an order of magnitude beyond current napkin math (~1,800 chunks) — reopen NG4 (vector DB) rather than silently degrading query performance.
- **ASK_FIRST:** Before the first live index build (confirm chunking output looks reasonable on a sample before committing to the full corpus). Before changing the locked embedding model, chunk size cap, or similarity threshold from their spec'd defaults. Before any edit to the existing `obsidian` entry in `~/.claude.json`, even incidental.

---

## 16) Changelog
See `meta/_changelog.md`.
