# GTM Engineering Portfolio — HeeGun Eom

**I'm a GTM operator who builds the AI systems that make sales and marketing teams faster.** I built the foundation, an AI-ready company knowledge base and a stack of custom MCP servers, and then the systems that run on it: AI-augmented attribution, account research, personalized outbound, and an AI-visibility (GEO) content engine. Built against a real go-to-market stack (CRM, outbound, ABM/intent, paid, call recordings, product analytics) and a production marketing site.

Most go-to-market work is described in decks. This is the work itself: production AI agents, infrastructure, and workflows I built and ran inside a B2B AI company's revenue org. It comes in two layers, a **foundation** (the context and tools AI needs) and the **systems** built on top, each solving a concrete GTM problem with the judgment of someone who has actually run pipeline.

> Sanitized for public sharing. Customer names, account IDs, credentials, and confidential corpus contents have been removed. The engineering, architecture, and logic are intact.

---

## At a glance

Two foundation layers (the context and tools AI needs) under five production systems. Everything below was built and run inside a B2B AI company's revenue org.

| | Piece | What it is | Headline result |
|---|-------|------------|-----------------|
| 🧠 Foundation | [Second Brain](./second-brain/) | AI-ready company knowledge base (Obsidian) | ~340 evidence-backed docs, structured for AI retrieval |
| 🔌 Foundation | [GTM MCP Stack](./mcp-stack/) | Custom + composed MCP servers | 5 custom servers (HubSpot, Outreach, LinkedIn, Unify) on Cloud Run |
| ⭐ System | [Attribution Engine](./attribution-engine/) | 7-channel demo-attribution agent | **~40%** of "Direct" deals re-attributed; 30-60 min → **5-10 min** |
| System | [Account-Research Agent](./account-research-agent/) | Multi-agent AE call prep | pre-call research **1-3 hrs → 5-10 min** |
| System | [Personalized Outbound](./personalized-outbound/) | 19-persona cold-email system | reply rate **~3% → ~9%** |
| System | [GEO Content Engine](./geo-content-engine/) | AI-visibility glossary program | **~100** AI-citable pages · **~339K** monthly searches · 12-agent build |
| System | [Interactive Demos & Animations](./interactive-demos/) | Vibe-coded product demos + animations on a production site | **#1 contributor** to the home product UI · 20 animation components, live |

**Who:** GTM operator (sales + marketing + hands-on AI) · 📍 SF · open to GTM Engineer / GTM Lead.
**Contact:** heeguneom@gmail.com · 415-819-2176 · [LinkedIn](https://www.linkedin.com/in/heeguneom/) · Full detail below.

---

## Foundation — the two layers AI-native GTM runs on

### A. [Second Brain](./second-brain/) — the context layer
An AI-ready company knowledge base: ~340 evidence-backed documents in an Obsidian vault, organized into 6 GTM/marketing domains, so AI agents and new projects start from grounded company context instead of a blank page. Every project follows one disciplined pattern (rubric → primary-source evidence → synthesis, with discoverable frontmatter), so the corpus compounds and each document strengthens the others.

**What it is:** context engineering for AI · ~340 docs · 32 evidence-backed projects · structured for retrieval
**Why it matters:** agents are only as good as what they know about the company. This is what they know.

### B. [GTM MCP Stack](./mcp-stack/) — the tool layer
I **built custom MCP servers** (HubSpot, Unify GTM, Outreach, LinkedIn Ads) that expose the go-to-market stack to AI agents as callable tools, and **built agents and skills on top of published MCPs** (Apollo, PostHog, Crustdata, Clay, Google Ads), orchestrating several at once. Several are deployed to Google Cloud Run to handle OAuth token exchange server-side.

**Stack:** TypeScript MCP servers · typed REST clients + tool schemas · OAuth / token auth · stdio + HTTP · Cloud Run
**Why it matters:** agents are only as capable as the tools they can call. This is what they can do.

---

## Systems — built on the foundation

### 1. [Multi-Channel Demo Attribution Engine](./attribution-engine/) — flagship
An AI agent that traces how a demo booking was *actually* sourced by cross-referencing **seven GTM channels** (CRM, outbound, ABM/intent, Google Ads, LinkedIn Ads, call recordings, product analytics), then resolves their contradictions into one defensible attribution call with a confidence rating.

The hard part is not the plumbing, it's the judgment: the CRM reports "Direct" for deals that were really outbound-sourced, outbound targets one persona while a colleague books, and the strongest signal (a prospect saying "your team emailed me" on a call) lives where no dashboard reads. The engine encodes a nine-tier evidence-priority hierarchy to get this right.

**Stack:** Claude agent orchestration · HogQL · GAQL · CRM/outbound/ABM APIs · MCP integrations
**Impact:** attribution cut from ~30-60 min/deal to ~5-10 min (one reusable prompt) · ~40% of "Direct" deals re-attributed to outbound/paid · ran across a full year of bookings

### 2. [AI Account-Research Agent](./account-research-agent/)
A multi-agent system that preps AEs before a call by pulling deal context from call recordings, email, and team chat, enriching the account, then fanning out 6-8 parallel research agents into the company. Turns hours of pre-call prep into minutes, and turns facts into talk tracks, objection handling, and an expansion path.

**Stack:** Multi-agent fan-out · call-recording + comms search · enrichment APIs · web research
**Impact:** pre-call research cut from ~1-3 hrs to ~5-10 min · adopted across every active deal the AE team worked

### 3. [AI Personalized Outbound at Scale](./personalized-outbound/)
A persona-aware cold-email system covering 19 B2B buyer archetypes that enriches a prospect from a single LinkedIn URL (career history, recent posts) and generates first-touch and follow-up messaging tailored to the persona, with a hard guardrail that keeps the voice human so personalization survives scale instead of collapsing into mail-merge.

**Stack:** LinkedIn enrichment · persona library · capability/proof mapping · LLM generation with a voice guardrail
**Impact:** personalized first-touch in ~1-2 min vs 15-20 min manual · reply rate ~3% → ~9%

### 4. [GEO Content Engine](./geo-content-engine/) — AI-visibility glossary
The marketing side of the same skill set. I audited a site's search + AI-visibility footprint (Semrush MCP), defined a citation-optimized content strategy from published GEO research, generated a ~100-term glossary by orchestrating **12 nested Claude instances** (each running per-term research), verified it, and shipped it to a production Next.js site as MDX pages with full AI-citation structured data.

**Stack:** Semrush MCP · /technical-research · /nest-claude (12-agent fleet) · /audit · Next.js / MDX + JSON-LD
**Impact:** ~100 AI-citable pages shipped · ~339K monthly searches targeted · full FAQ/DefinedTerm/HowTo schema

### 5. [Interactive Product Demos & Animations](./interactive-demos/)
The front-end side of marketing engineering. I vibe-coded a large part of a production marketing site, the interactive product demos and the animated product visualizations: I owned the product story, built the interactive mock-ups, and shipped production-ready React components, with the design team polishing the final visuals. Verifiable in git: **#1 contributor to the home-page product UI** (187 repo commits overall).

**Stack:** Next.js / React / TypeScript · CSS keyframes + modules · Motion · Rive (WASM) · Arcade · AI-assisted (vibe) coding
**Impact:** 20 product-animation components + interactive demos live on the homepage and four persona use-case pages

---

## What this body of work demonstrates

- **Context engineering for AI:** structuring company knowledge so agents can retrieve and reason over it, the prerequisite for any serious AI-native GTM motion.
- **Revenue infrastructure built with AI**, shipped and used, not theorized.
- Fluency across the **full modern GTM stack** and the APIs and query languages behind each tool.
- **GTM judgment** — knowing which signals to trust and why — which is the part that cannot be automated without understanding the work.
- An **engineering mindset**: deterministic flows, graceful failure handling, and correctness on the small things that quietly break go-to-market systems.

## Background

GTM operator and BDR hiring manager at a B2B AI developer-tools company. Combined background in sales, marketing, and hands-on AI: I both run the go-to-market motion and build the AI systems that power it.

📍 San Francisco · Open to GTM Engineer / GTM Lead roles at AI-native companies.

**Contact:** heeguneom@gmail.com · 415-819-2176 · [LinkedIn](https://www.linkedin.com/in/heeguneom/)
