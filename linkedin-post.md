# LinkedIn build-in-public post

> Readable version of the portfolio for the GTM-Lead audience who won't open a repo.
> Anchored on the strongest concrete story (attribution), then zooms out to the two-layer body of work.
> Tip: keep the one link (to the repo) in the first comment, not the post body, so reach isn't throttled.

---

Our CRM kept telling us demos were "Direct."

They weren't.

A prospect would book a demo, HubSpot would stamp it "Direct," and leadership would read that as "organic, we didn't pay for it." Meanwhile an outbound sequence had touched a colleague at that company three weeks earlier, and a paid campaign had run in the same window. The outbound and paid teams got zero credit for pipeline they actually created.

The problem: no single tool sees the whole journey. The truth is scattered across the CRM, the outbound platform, the ABM tool, two ad platforms, the call recordings, and product analytics.

So I built an AI agent that traces a booking across all seven, in 5-10 minutes, off a single reusable prompt. It surfaced that ~40% of the deals we'd been calling "Direct" were actually outbound- or paid-sourced. That changed how we credited channels and where we put budget.

But the attribution agent is just one system. The part I'm most proud of is the layer underneath it.

To build AI that can actually run a GTM motion, you need two things most teams don't have:

→ Context: I built an AI-ready company knowledge base, ~340 evidence-backed docs, so agents start from grounded company knowledge instead of a blank page.

→ Tools: I built a stack of custom MCP servers (HubSpot, Outreach, LinkedIn Ads, Unify) so agents can actually operate the GTM stack, deployed to the cloud to handle the OAuth piece.

Then the systems on top write themselves:
• demo attribution across 7 channels
• an account-research agent that preps AEs in minutes
• personalized outbound that tripled reply rates (3% → 9%)
• a GEO content engine: ~100 AI-citable pages, built by orchestrating 12 AI agents

Two lessons that stuck with me:

1. AI didn't replace the GTM thinking. It scaled it.

2. The leverage isn't in any one agent. It's in the foundation, the context and tools, that lets you build the next ten.

This is the work I love: building the AI systems, and the foundation under them, that make a sales and marketing team faster and smarter.

Full writeup + sanitized code in the comments. 👇

#GTM #RevOps #AI #GTMEngineering #GEO
