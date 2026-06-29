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

## Published servers I configured into the stack

To round out coverage, the same config wires in published MCP servers I did not author but integrated and credentialed: **Apollo** (sales-intelligence enrichment + search), **PostHog** (product analytics via HogQL), and **Google Ads** (paid-search analytics via GAQL).

## The integration surface (why this matters)

Together, the stack gives an agent a single operating surface across the entire funnel:

```
        ┌─────────────────────────── AI agent ───────────────────────────┐
        │                                                                 │
   CRM (HubSpot)   Outbound (Outreach)   ABM/Intent (Unify)   Paid (LinkedIn, Google)   Analytics (PostHog)
   [custom]        [custom]              [custom]             [custom + published]       [published]
```

That coverage is exactly what lets one agent do cross-channel work no single tool can: trace a demo across seven systems (attribution engine), pull deal context from calls + CRM + enrichment (account research), or enrich a prospect and act on a sequence (outbound).

## What this demonstrates

- **Hands-on protocol + API engineering:** building MCP servers in TypeScript, wrapping REST APIs with typed clients and tool schemas, handling OAuth and token-based auth.
- **Systems thinking:** treating the GTM stack as one programmable surface rather than a set of disconnected SaaS tools.
- **The foundation for AI-native GTM:** agents are only as capable as the tools they can call. Building those tools is the GTM-engineering work underneath everything else in this portfolio.
