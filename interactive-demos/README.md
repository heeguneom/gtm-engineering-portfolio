# Interactive Product Demos & Animations

I vibe-coded a large part of a B2B AI company's production marketing site: the interactive product demos and the animated product visualizations. I owned the product story, built the interactive mock-ups, and shipped production-ready React components; the company's designers then polished the final visual design.

> Collaborative work on a private company codebase. This describes my contribution and points to the live result; the source is not reproduced here. Authorship is verifiable in the repo's git history.

---

## What I did

The job was to turn an abstract product into a marketing site people actually understand by *showing* it, not describing it. My part of that:

1. **Laid out the product story** — the narrative arc of the homepage and use-case pages: what each section needs to prove, in what order, to which persona (documentation, support, product, and GTM leaders).
2. **Built the interactive mock-ups** — translated that story into working, clickable interaction designs rather than static comps.
3. **Vibe-coded it to production** — used AI-assisted coding to ship real, production-ready React/Next.js components: the interactive demos and the animated product visualizations that run on the live site.
4. **Handed off for polish** — the design team refined the final visuals (spacing, color, type). I owned the story, the interaction, and the working implementation.

## What shipped

Verifiable in git: I'm the **#1 contributor to the home-page product UI** (~116 commits to `(home)/_components`, ahead of every other contributor), and **187 commits** across the repo overall.

- **Animated product visualizations (20 animation components)** in the home page that bring the product to life: the hero animation, the "three pillars" section (Ask AI, Copilot, KB-updater), and the developer-section sequence (Workflows, APIs, Schedules & Triggers, Governance, Analytics, Evals, Traces, Connectors).
- **Interactive demos** embedded across the homepage and use-case pages (Arcade walkthroughs + interactive-demo CTAs on the three pillars).
- **Rive (WASM) animations** for richer, runtime-interactive product graphics, including the rendering/CSP setup to serve them.
- **Use-case pages (v2)** for documentation, support, product, and GTM-leader personas, each with its own narrative and demos.
- Plus the polish that production demands: fixing layout shift, animation timing, mobile-first demo layout, and hydration.

## Tech

- **Next.js / React / TypeScript** — the production marketing site
- **CSS `@keyframes` + CSS modules** — hand-built animations with layout-shift control
- **Motion (`motion/react`)** — declarative animation
- **Rive (`@rive-app/react-canvas`, WASM)** — interactive, runtime product animations
- **Arcade** — embedded interactive product demos

## What this demonstrates

- **Story to shipped code, the full loop:** I can take a product narrative, design the interaction, and implement it in production, not hand off a wireframe and hope.
- **Vibe coding to a real bar:** AI-assisted front-end development that survived code review and runs on a live, public marketing site, including the unglamorous production work (layout shift, hydration, mobile, performance).
- **Product storytelling:** structuring how an abstract AI product is explained and demonstrated to four distinct buyer personas.

> Live proof beats any description for this one. Recommended: link the live homepage and use-case pages here so a reviewer can see the demos and animations running. (Holding the URL out by default to stay consistent with the rest of this repo, which generalizes the employer, your call to add it.)
