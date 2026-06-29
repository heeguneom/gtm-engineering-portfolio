# GTM MCP Stack — Custom Servers

The infrastructure layer under the other three systems. I built a set of **Model Context Protocol (MCP) servers** that give AI agents secure, programmatic access to the go-to-market stack, then wired them together with published servers into one configuration an agent can operate across.

This is what made the attribution engine, account-research agent, and personalized-outbound system possible: an agent can only act on the GTM stack if something exposes that stack to it as tools. These servers are that something.

> Config sanitized: every credential is a `${ENV_VAR}` placeholder, paths are relative, no real tokens or hosted URLs. See [mcp.config.example.json](./mcp.config.example.json). Server source is not included (employer-built code).

---

## What an MCP server is (one line)

MCP is the open standard for exposing a system's capabilities to an AI agent as callable tools. An MCP server wraps an API (HubSpot, Outreach, etc.) and presents its operations as tools the agent can invoke, with auth handled server-side.

## Servers I built

| Server | Wraps | Representative tools exposed to the agent |
|--------|-------|-------------------------------------------|
| **hubspot-admin** | HubSpot CRM (admin-level) | create/update/list properties and pipelines, owner reassignment (single + bulk), record counts by owner, audit logs, property history |
| **unifygtm** | Unify GTM Data API | list objects, list/get records, find-unique by field, create objects and records |
| **outreach** | Outreach.io API | search prospects, list sequences, sequence performance + states, mailings, sequence comparison |
| **linkedin-ads** | LinkedIn Marketing API | account summary, list campaigns + campaign groups, campaign analytics, creatives, conversion tracking |

I built the Outreach server in two transports: a **stdio** server for local agent use and an **HTTP** server (`outreach-mcp-http`) for remote/hosted access. All are TypeScript (server + typed API client + tool definitions).

## Published MCPs I built agents and skills on top of

I did not author these, but I integrated, credentialed, and orchestrated them, building agents and skills that compose them into workflows:

- **Apollo** — sales-intelligence enrichment + people/company search (powers account research and attribution)
- **PostHog** — product analytics via HogQL (powers the attribution engine's website-journey step)
- **Crustdata** — LinkedIn person/company enrichment + recent posts (powers the personalized-outbound enrichment)
- **Clay** — AI-native GTM data enrichment and workflow tooling
- **Google Ads** — paid-search analytics via GAQL (the paid-conversion window in attribution)

The engineering here is composition, not authorship: building agents and skills that orchestrate several published MCPs together into something none of them does alone.

## Deployment & the OAuth token-exchange problem

Several of these APIs (Outreach, LinkedIn Ads, Google Ads) use OAuth 2.0, which created a real problem for a local stdio MCP server. OAuth's authorization-code flow needs a **stable, public redirect URI**, and access tokens have to be **refreshed on a schedule**. Running that locally meant tunneling an OAuth callback through ngrok and managing refresh tokens on disk, fragile, and not something you can hand to a teammate.

The fix: I deployed the HTTP-transport MCP servers to **Google Cloud Run**. The hosted service:

- owns a **stable public URL**, so it can serve as the OAuth redirect URI (no ngrok tunnel)
- performs the **authorization-code and refresh-token exchange server-side**, keeping long-lived credentials off local machines
- exposes the MCP endpoint behind a **bearer token**, so an agent connects to one authenticated URL

In practice the agent config points at a `https://<service>-<id>.<region>.run.app/mcp` endpoint instead of spawning a local process, and the entire OAuth lifecycle is handled in the cloud. This is what made the Outreach, LinkedIn Ads, and Google Ads integrations reliable enough to build agents on top of. (An earlier `outreach-mcp-http` variant runs the same idea on Vercel serverless functions.)

## The integration surface (why this matters)

Together, the stack gives an agent a single operating surface across the entire funnel:

```
             ┌──────────────────────── AI agent ────────────────────────┐
             │                                                          │
 CRM         Outbound     ABM/Intent   Enrichment                Paid              Analytics
 (HubSpot)   (Outreach)   (Unify)      (Apollo/Crustdata/Clay)   (LinkedIn,Google) (PostHog)
 [built]     [built]      [built]      [built on top of]         [built+published] [built on top of]
```

That coverage is exactly what lets one agent do cross-channel work no single tool can: trace a demo across seven systems (attribution engine), pull deal context from calls + CRM + enrichment (account research), or enrich a prospect and act on a sequence (outbound).

## What this demonstrates

- **Hands-on protocol + API engineering:** building MCP servers in TypeScript, wrapping REST APIs with typed clients and tool schemas, handling OAuth and token-based auth.
- **Cloud deployment + auth engineering:** deploying MCP servers to Google Cloud Run (and Vercel) to solve OAuth's public-redirect and token-refresh constraints server-side, behind bearer auth, so integrations are reliable and shareable rather than local and fragile.
- **Composition over authorship:** building agents and skills on top of published MCPs (Apollo, Crustdata, Clay, PostHog) and orchestrating several at once into workflows none performs alone.
- **Systems thinking:** treating the GTM stack as one programmable surface rather than a set of disconnected SaaS tools.
- **The foundation for AI-native GTM:** agents are only as capable as the tools they can call. Building and composing those tools is the GTM-engineering work underneath everything else in this portfolio.
