<!--
Portfolio copy of a skill I built (account-research). Sanitized for public sharing:
company name, AE names, and customer names replaced with placeholders.
Implemented against a real GTM stack (call recordings, email, team chat,
sales-intel enrichment, web research) via MCP tools.
-->

---
name: account-research
description: "Research accounts and deals for AEs. Pulls context from Gong calls, Gmail, Slack, and Apollo, then runs deep company research using parallel agents. Produces deal reports, strategic intelligence, and account-specific analysis. Use when asked to 'research [account]', 'summarize the [account] deal', 'what do we know about [account]', or 'full research on [account]'."
argument-hint: "[account name] [research type or specific question]"
---

# Account Research

Research accounts and deals by gathering internal context (Gong, Gmail, Slack, Apollo) and external intelligence (financials, strategy, leadership, pain points, competitive landscape). Produces actionable reports with talk tracks, deal blockers, and expansion opportunities.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| **Account name** | Yes | "Acme", "Globex", "Initech" |
| **AE name** | Yes (ask if not provided) | "alex", "sam", "jordan" |
| **Research type** | Yes (ask if not provided) | See table below |
| **Specific question** | Only for "specific-question" type | "Does Acme use [Helpdesk]? Are they investing in AI for support?" |

### Research types

| Type | Trigger phrases | What it produces |
|---|---|---|
| **deal-summary** | "summarize the deal", "deal report", "what happened on calls" | Gong call synthesis + deal status report |
| **deep-research** | "research [account]", "deep dive on [account]" | Full strategic intelligence (financials, AI strategy, org structure, pain points, competitive) |
| **specific-question** | Any specific question about the account | Targeted research report on that question |
| **full-package** | "full research on [account]", "everything on [account]" | Deal summary + deep research + any specific questions |

---

## Output

All reports save to: `gtm-reports/{ae-name}/{account}/`

| Research type | Filename |
|---|---|
| Deal Summary | `DEAL-REPORT.md` |
| Deep Research | `{ACCOUNT}-DEEP-RESEARCH.md` |
| Specific question | `{descriptive-name}.md` (e.g., `Acme-AI-SUPPORT-STRATEGY.md`) |

---

## Workflow

### Phase 1: Gather internal context (always do this first)

Internal context comes before external research. The AE's own interactions contain deal-specific intelligence no web search can find.

**Step 1: Gong calls**

Search for all calls mentioning the account:

```
mcp__gong__search_calls - paginate through all results, scanning titles for the account name
```

For each matching call:
1. Get the **summary** first (`mcp__gong__get_call_summary`) - this is cheaper and usually sufficient
2. Get the **full transcript** (`mcp__gong__get_call_transcript`) only for the most important calls (demos, pricing discussions, executive calls)

Extract from each call:
- What the account needs (stated pain points, requirements)
- What was demonstrated or discussed
- Pricing mentioned
- Objections or blockers raised
- Key quotes from the prospect (verbatim)
- Next steps committed to
- Who attended (names, titles, roles)

**Step 2: Gmail (if available)**

```
mcp__claude_ai_Gmail__* - Search for email threads with the account domain
```

Look for:
- Proposals or quotes sent
- Objections raised via email
- Follow-up commitments
- Pricing discussions
- Security questionnaires or procurement documents
- Internal team discussions forwarded

**Step 3: Slack (if available)**

```
mcp__claude_ai_Slack__* - Search internal channels for the account name
```

Look for:
- Deal strategy discussions between AEs and leadership
- Technical questions from the prospect relayed internally
- Notes from calls not recorded in Gong
- Competitive intel shared by the team
- Blockers or escalations

**Step 4: Apollo**

```
mcp__apollo-io__enrich_company - Get company details
mcp__apollo-io__search_people - Find key contacts and org chart
```

Enrich with:
- Company size, industry, revenue, funding
- Key contacts beyond the primary (find the CIO, CTO, VP Engineering, Head of Support)
- Org structure clues (who reports to whom)

---

### Phase 2: Synthesize Deal Summary

If the research type is "deal-summary" or "full-package", write `DEAL-REPORT.md` with this structure:

```markdown
# {Account} Deal Report

**Account:** {company name}
**Primary Contact:** {name, title}
**[Company] Team:** {AE, engineers, executives involved}
**Report Date:** {today}
**Source:** {N} Gong calls + Gmail + Slack

---

## Deal Summary
{2-3 paragraph overview: what stage, estimated ACV, timeline}

## What {Account} Needs
### Core use case
### Data sources / integrations
### Must-have capabilities (stated by prospect)
### Nice-to-have (expressed interest)

## What Happened on Each Call
### Call 1: {title} ({date} - {duration})
{Key moments, numbered list}
### Call 2: ...

## Deal Blockers (ranked by severity)
### 1. {blocker} (HIGH/MEDIUM/LOW)
**Mitigation:** {what to do}

## Competitive Landscape
{What other vendors are they evaluating? Any named?}

## Buying Signals
| Signal | Strength | Evidence |

## Risk Signals
| Signal | Severity | Evidence |

## Recommended Next Steps
### Immediate (this week)
### Short-term (next 1-2 weeks)
### Medium-term (evaluation period)

## Pricing Summary
| Component | Cost | Notes |

## Key Quotes from {Contact}
> "{quote}" (context)

## Gong Call References
| Call | Date | Duration | ID | Link |
```

---

### Phase 3: Deep Research (parallel agents)

If the research type is "deep-research" or "full-package", launch parallel background agents to research the account.

**This phase MUST use the Agent tool with `run_in_background: true` to run 6-8 research agents simultaneously.** Do not research dimensions sequentially - the parallel approach is 5-8x faster.

#### Standard research dimensions

Adapt these based on what's relevant for the account. Not every dimension applies to every company.

| # | Dimension | What to find | Agent prompt focus |
|---|---|---|---|
| 1 | **Financial overview** | Revenue, key metrics, earnings, strategy priorities, digital investment mentions | Annual report, quarterly earnings, investor presentations. For US companies: 10-K/10-Q. For European: annual report. |
| 2 | **AI / technology strategy** | What leadership says about AI, partnerships, investments, press releases | CEO/CTO interviews, conference talks, press releases mentioning AI, automation, digital transformation |
| 3 | **Product / platform analysis** | What the account sells, developer portal, docs quality, support model | Visit their developer docs, API catalog, support pages. Assess documentation quality and gaps. |
| 4 | **Organizational structure** | Divisions, decision-makers, CIOs/CTOs, how purchases get approved | Board of management, leadership team, org chart, CIO/CTO names |
| 5 | **Pain points** | Developer complaints, support issues, product friction, community sentiment | Stack Overflow, Reddit, GitHub issues, developer forums, G2/Capterra reviews |
| 6 | **Competitive landscape** | How their competitors handle developer experience, who has AI docs | Compare 3-5 direct competitors on developer experience, AI features, documentation quality |
| 7 | **Account-specific** | Varies per deal | Tailor to what emerged from Gong calls (e.g., "AI in support strategy", "[Helpdesk] usage", "GDPR compliance") |

#### How to launch agents

For each dimension, launch a background agent:

```
Agent({
  description: "{Account} {dimension}",
  prompt: "Research {specific instructions for this dimension}. Report findings in structured format with specific numbers, quotes, and sources. Under 800 words.",
  run_in_background: true
})
```

Launch ALL agents in a single message (parallel, not sequential). Then wait for all to complete before synthesizing.

#### Synthesis

Once all agents report back, synthesize into `{ACCOUNT}-DEEP-RESEARCH.md` with this structure:

```markdown
# {Account} Deep Research: Strategic Intelligence for [Company] Deal

**Account:** {company} ({ticker if public})
**Deal Contact:** {name, title}
**Report Date:** {today}
**Sources:** {what was researched}

---

## Executive Summary for {AE name}
{3-4 paragraphs: key findings, critical insight, threat/opportunity, what this means for the deal}

## Part 1: Financial Overview
{Revenue, divisions, strategy, key numbers}

## Part 2: AI / Technology Strategy
### What Leadership Is Saying
{Direct quotes from CEO/CTO with dates}
### Active AI Deployments
{Table of what AI they're already using}
### Investment Scale
{Numbers on tech spending}

## Part 3: Product / Platform Analysis
{Their developer portal, APIs, docs quality, support model}
### The Problems [Company] Solves
{Specific pain points with evidence}

## Part 4: Organizational Structure
{Divisions, CIOs, decision-making process}
### Key People
{Names, titles, relevance to the deal}

## Part 5: Pain Points (with evidence)
{Developer complaints, support issues - specific quotes and links}

## Part 6: Competitive Landscape
{How competitors compare on developer experience and AI}

## Part 7: How [Company] Helps {Account}
### Strategic Alignment
| {Account} Priority | What Leadership Says | How [Company] Helps |
### The Business Case
{Cost justification, competitive justification, internal vs external}
### Expansion Opportunity
{Phase 1 -> Phase 2 -> Phase 3 with pricing}

## Part 8: Talk Track for {AE}'s Next Call
### Opening
{Suggested opening that references account-specific intelligence}
### Key talking points
{3-5 numbered points with evidence}
### Handling objections
{For each known blocker, provide the counter-argument}

## Sources
{Grouped by category with links}
```

---

### Phase 4: Specific Questions (on-demand)

If the AE asks a specific question, launch a focused research agent:

1. Use the deal context from Phase 1 (Gong, Gmail, Slack) to understand what's relevant
2. Launch a single deep agent targeting the specific question
3. Search: annual report, earnings calls, executive interviews/podcasts, press releases, blog posts, product pages
4. Write a focused report with the descriptive filename

The report should include:
- Direct evidence (quotes, numbers, links)
- Gap analysis (where the account has the capability vs where it's missing)
- Business case narrative (how to use this information in the deal)

---

## MCP Tool Reference

### Gong (`mcp__gong__*`)

| Tool | Use for |
|---|---|
| `search_calls` | Find all calls for an account. Paginate - results come in batches of 100. Scan titles for account name. |
| `get_call_summary` | AI-generated summary with key points, topics, action items. Use this first - cheaper than transcripts. |
| `get_call_transcript` | Full speaker-attributed transcript. Use for key calls when you need exact quotes. Set `maxLength` to 50000 for full transcripts. |
| `list_calls` | List recent calls. Less flexible than search_calls. |

**Gong pagination:** search_calls returns 100 calls per page with a cursor. Always check if there are more results and paginate through ALL pages to find the account's calls.

### Gmail (`mcp__claude_ai_Gmail__*`)

Search for threads with the account's domain or contact names. Gmail MCP may require authentication - if it fails, note it and continue with other sources.

### Slack (`mcp__claude_ai_Slack__*`)

Search for the account name in internal channels. Slack MCP may require authentication - if it fails, note it and continue.

### Apollo (`mcp__apollo-io__*`)

| Tool | Use for |
|---|---|
| `enrich_company` | Company size, revenue, industry, tech stack |
| `search_people` | Find contacts by title at the account |
| `enrich_person` | Get details on a specific contact |

### Web (WebFetch, WebSearch)

Use for all external research: company websites, annual reports, press releases, earnings transcripts, developer portals, Stack Overflow, Reddit, GitHub.

---

## Key Principles

1. **Internal first, external second.** Gong calls, Gmail, and Slack contain deal-specific context no web search can find. Always start there.

2. **Use the account's own language.** If their CEO says "digital by default," use that phrase. If they call their initiative "Strategy 2030," reference it by name. Mirror their terminology in talk tracks.

3. **Be specific with numbers.** Revenue figures, employee counts, API counts, outage counts, support ticket volumes. Vague claims ("large company with many APIs") are useless. Specific claims ("EUR 82.9B revenue, 15-20 APIs across 6 divisions, 1,200+ recorded outages") are actionable.

4. **Include honest risk assessment.** Don't just surface buying signals. Flag deal risks, competitive threats, and internal blockers. AEs need the full picture.

5. **Every finding needs a "so what."** Don't just report facts. Connect every finding to: what should the AE say, how does this help the deal, what objection does this address.

6. **Parallel research is mandatory for deep research.** Launch 6-8 background agents simultaneously. Sequential research is 5-8x slower and blocks the AE.

7. **Quotes are gold.** Direct quotes from the prospect (Gong) and from the account's leadership (press/interviews) are the most valuable content. Surface them prominently.

---

## Examples

### Good invocation
```
/account-research Acme - full package, AE is Alex
/account-research Globex - deal summary only, AE is Sam
/account-research Initech - does Initech use any AI for their docs? AE is Jordan
/account-research Umbrella - deep research, AE is Alex
```

### Good output characteristics
- Report starts with an executive summary the AE can skim in 2 minutes
- Every section has specific evidence (quotes, numbers, links)
- Talk track uses the account's own strategic language
- Objection handling is tied to specific evidence ("When they say X, respond with Y because their CEO said Z")
- Expansion path has concrete pricing tiers

### Avoid
- Generic summaries without account-specific evidence
- Reporting facts without connecting them to the deal
- Skipping internal context (Gong/Gmail/Slack) and going straight to web research
- Running research dimensions sequentially instead of in parallel
- Reports without talk tracks or next steps
