# GTM Engineering Portfolio — HeeGun Eom

**I'm a GTM operator who builds the AI systems that make sales and marketing teams faster:** AI-augmented attribution, account research, and personalized outbound, built against a real go-to-market stack (CRM, outbound, ABM/intent, paid, call recordings, product analytics).

Most go-to-market work is described in decks. This is the work itself: production AI agents and workflows I built and ran inside a B2B AI company's revenue org. Each system below solved a concrete GTM problem, integrates multiple platforms through their APIs, and encodes the judgment of someone who has actually run pipeline.

> Sanitized for public sharing. Customer names, account IDs, and credentials have been removed. The engineering, integration surface, and logic are intact.

---

## The systems

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

---

## What this body of work demonstrates

- **Revenue infrastructure built with AI**, shipped and used, not theorized.
- Fluency across the **full modern GTM stack** and the APIs and query languages behind each tool.
- **GTM judgment** — knowing which signals to trust and why — which is the part that cannot be automated without understanding the work.
- An **engineering mindset**: deterministic flows, graceful failure handling, and correctness on the small things that quietly break go-to-market systems.

## Background

GTM operator and BDR hiring manager at a B2B AI developer-tools company. Combined background in sales, marketing, and hands-on AI: I both run the go-to-market motion and build the AI systems that power it.

📍 San Francisco · Open to GTM Engineer / GTM Lead roles at AI-native companies.
