# LinkedIn build-in-public post (flagship: attribution engine)

> Readable version of the flagship for the GTM-Lead audience who won't open a repo.
> Fill in the [bracketed] numbers before posting. Keep one link (to the repo) in the first comment, not the post body, so reach isn't throttled.

---

Our CRM kept telling us demos were "Direct."

They weren't.

A prospect would book a demo, HubSpot would stamp it "Direct," and leadership would read that as "organic, we didn't pay for it." Meanwhile an outbound sequence had touched a colleague at that same company three weeks earlier, and a paid campaign had run in the same window. The outbound and paid teams got zero credit for pipeline they actually created.

The problem: no single tool sees the whole journey. The truth is scattered across the CRM, the outbound platform, the ABM tool, two ad platforms, the call recordings, and product analytics. Stitching it together by hand took ~30-60 minutes per deal, and still missed the cross-contact outbound touches.

So I built an AI agent that does it in [X] minutes.

Give it a domain or an email, and it traces the booking across all seven channels, then resolves the contradictions with a priority hierarchy that ranks evidence by quality:

→ A prospect saying "your team emailed me" on a recorded call beats a UTM tag.
→ A UTM tag beats an ABM play.
→ An ABM play beats whatever the CRM guessed.

The most useful thing it surfaced wasn't a number. It was a pattern: [X]% of the deals we'd been calling "Direct" were actually outbound- or paid-sourced. That changed how we credited channels and where we put budget.

Two lessons that stuck with me:

1. The plumbing is the easy part. The hard part is the judgment about which signal to trust. You can't automate that without understanding the work.

2. AI didn't replace the GTM thinking. It scaled it.

This is the kind of thing I love building: the AI systems that make a sales and marketing team faster and smarter.

Writeup + sanitized code in the comments. 👇

#GTM #RevOps #AI #GTMEngineering #Attribution
