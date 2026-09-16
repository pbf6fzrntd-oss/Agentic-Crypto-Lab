# Battlecard: Monid (monid.ai)

**Last checked: 2026-09-16**
**Relationship to Shredly: adjacent/overlapping, not a direct head-to-head competitor.** See "Where they win / honest gaps" below before using this in outbound or content — do not frame Monid as a straight alternative to Shredly.

## Summary

Monid markets itself as "OpenRouter for agent tools" — a hosted registry/router that lets an AI agent discover, inspect, run, and pay for *third-party* tools and data APIs (search, SEO, ecommerce, lead-gen, market data, social data, media generation, blockchain data, etc.) at runtime, from one account and one balance, with no per-tool subscriptions ([monid.ai/openrouter-for-agent-tools](https://monid.ai/openrouter-for-agent-tools), accessed via search cache 2026-09-16). Monid itself exposes an MCP server (`https://mcp.monid.ai/v1`) plus a "skill" and direct API, so an MCP client (Claude, ChatGPT, Cursor, etc.) or agent framework connects to Monid and gets routed access to its whole catalog ([docs.monid.ai quickstart, via search cache](https://docs.monid.ai/guide/quickstart-skill.html), 2026-09-16).

**Core model difference from Shredly:** Monid's business is aggregating and routing calls across *many other companies' tools* it doesn't own — it's a marketplace/router layer sitting in front of third-party APIs. Shredly's business is hosting an MCP server in front of *one customer's own* API, database, or internal tool. A prospect asking "how do I get my own API in front of agents" needs Shredly; a prospect asking "how do I give my agent one connection to hundreds of existing public APIs" is Monid's use case. These are different jobs that both happen to speak MCP.

Founded by Shengkun Ye and Feiyou Guo (both University of Washington grads; Ye previously worked at Founders Inc, TabaPay, and WeChat), based in San Francisco. Launched April 2026, relaunched as "Monid 2.0" in May 2026 ([search results citing Crunchbase/LinkedIn profiles](https://www.crunchbase.com/organization/monid), 2026-09-16). Raised $2.1M pre-seed from 1984 Ventures, Llama Ventures, Untapped Capital, and Founders, Inc. (announced late August/early September 2026) ([Dealroom news item](https://dealroom.co/news/148133-monid-raises-2-1m-to-let-ai-agents-buy-tools-on-demand/), via search cache 2026-09-16; [WOWTALE](https://en.wowtale.net/2026/09/01/234971/), 2026-09-01; [TheSaaSNews](https://www.thesaasnews.com/news/monid-raises-2-1m-pre-seed/), via search cache). Reports 4M+ agent transactions processed and a catalog of 1,700+ tools from 55 providers, per company/press statements as of ~September 2026 ([search cache summarizing Crunchbase/press coverage](https://www.crunchbase.com/organization/monid), 2026-09-16) — some secondary sources describe the catalog as "1,800+ tools/APIs," which reads as a rounded/later figure from the same "1,700+ tools, 55 providers" base rather than a contradiction; treat the specific count as time-sensitive and re-verify before quoting a number in a live deal.

**Note on sourcing:** I was unable to load monid.ai, docs.monid.ai, or most third-party coverage directly in this session (network egress to those domains was blocked for the fetch tool). The claims below are drawn from search-engine result snippets and cached summaries of those pages, not a live read of Monid's own site — flag this explicitly to whoever verifies pricing/features before a live deal, and treat every claim below as needing a fresh primary-source check.

## Pricing (source + date)

**Inferred/secondary-sourced, not confirmed against a live pricing page — re-verify at monid.ai before quoting.**

- No subscriptions or enterprise contracts. Pricing is per-tool: per-call (flat fee per execution, e.g. an example figure of ~$0.003/call cited) or per-result (fee per item returned), set by each endpoint/provider individually.
- Users/agents draw down a single prepaid balance; new accounts reportedly start with $1 of free credit.
- Per-search-cache examples cite call costs in fractions of a cent (e.g. "$0.0013" and "about a tenth of a cent" quoted in secondary coverage) — these read as illustrative examples from specific tools in the catalog, not a platform-wide flat rate.
- Source: search-engine cached summaries of [monid.ai/docs/guide/how-it-works](https://monid.ai/docs/guide/how-it-works) and secondary reviews (MOGE, aitoolly, Onei AI, opentools.ai) surfaced 2026-09-16 — none of these were loaded directly in this session; treat as **inferred, not confirmed from a direct primary-source read**.
- No evidence found of a flat monthly/subscription tier comparable to Shredly's Free / $10 Shared / $50 Private structure — Monid's model appears to be consumption-based per-call billing across its aggregated catalog rather than tiered hosting plans.

## Features

- Registry of 1,700+ tools across 55 providers spanning search, SEO, lead generation, ecommerce, market/financial data, social data, image/video/audio/3D generation, private-company intelligence, and blockchain/on-chain data (per press coverage, 2026-09).
- Agent-facing flow: discover (what's available for a task) → inspect (schema, pricing, docs) → run (structured input, get result) → pay (debited from one balance) — no per-tool sign-up or API key management for the agent's owner.
- Access methods: an MCP server endpoint (`https://mcp.monid.ai/v1`) for MCP-compatible clients (Claude.ai, ChatGPT, Cursor, etc.) via Streamable HTTP with no local install; a "skill" file (`monid.ai/SKILL.md`) for agent frameworks/CLIs; and a direct API for calling from code.
- No claim found (in the sources reviewed) that Monid hosts an MCP server *for a customer's own proprietary API* the way Shredly does — its MCP server is the front door to Monid's own aggregated catalog of third-party tools, not a wrapper you point at your own backend.
- Positions itself against subscription-based tool access generally ("no per-tool sign-ups and no subscriptions") rather than against MCP-hosting-for-your-own-API specifically.

## Where Shredly wins

- **Your own API/database as an MCP server.** Monid's catalog is other companies' public tools and data APIs — it has no mechanism (found in sources reviewed) for taking a customer's private REST API or database and exposing it as an MCP server for that customer's own agents/customers. That is Shredly's entire product.
- **Ownership and control of the served data.** With Shredly, the customer's own backend is the source of truth and Shredly runs the MCP layer in front of it; with Monid, the agent is calling third-party providers' endpoints that the customer doesn't control or own.
- **Simple flat pricing for a single tool.** Shredly's Free / $10 Shared / $50 Private tiers are flat and predictable for hosting one MCP server. Monid's model is consumption-based, per-call, across many tools — better suited to "give my agent access to a lot of existing external data" than to "put my one API behind MCP for a known/fixed cost."
- **SMB self-serve motion for a specific, known use case.** An AI-team lead who already has an API/database and just needs it reachable by agents gets there faster and more directly with Shredly than by adopting a many-tool router aimed at a different problem.

## Where they win / honest gaps

**Read this before using Monid in a comparison — it is not a straight substitute for Shredly.**

- Monid solves a genuinely different problem well: giving an agent broad, on-demand access to hundreds of *existing third-party* tools/APIs without the agent owner integrating each one individually. If a prospect's need is "my agent needs to call lots of external data sources I don't own," Monid (or a similar router) is the relevant category — Shredly does not compete there, since Shredly only hosts a customer's own API/database as an MCP server.
- Monid already speaks MCP (its own `mcp.monid.ai` endpoint) and reports real usage traction (4M+ agent transactions cited in press as of ~Sept 2026) and institutional pre-seed backing ($2.1M from 1984 Ventures, Llama Ventures, Untapped Capital, Founders Inc) — both facts should be repeated only with the sourcing caveats above, but they are the kind of traction/credibility signal worth acknowledging honestly rather than dismissing.
- Breadth of catalog (1,700+ tools, 55 providers) is a real differentiator for the "many tools, one connection" use case that no single-API MCP host, including Shredly, addresses.
- **Sales/content guidance:** Do not position Monid as a like-for-like alternative to Shredly in battlecards, outbound, or comparison content. Use it only when a prospect is explicitly weighing "one router for many existing tools" (Monid's category) against "host my own API/tool as its own MCP server" (Shredly's category) — and say so explicitly rather than implying they solve the same problem. Positioning Monid as a direct competitor would overstate overlap that doesn't hold up under a prospect's own research.

## Sources

- [monid.ai/openrouter-for-agent-tools](https://monid.ai/openrouter-for-agent-tools) — homepage/positioning copy, accessed via search-engine cache 2026-09-16 (direct fetch blocked in this session)
- [docs.monid.ai — Introduction / How It Works / Quickstart (Skill)](https://docs.monid.ai/) — product mechanics, MCP endpoint, pricing model, accessed via search-engine cache 2026-09-16 (direct fetch blocked in this session)
- [Dealroom: "Monid raises $2.1M to let AI agents buy tools on demand"](https://dealroom.co/news/148133-monid-raises-2-1m-to-let-ai-agents-buy-tools-on-demand/) — funding round, investors, traction figures, accessed via search-engine cache 2026-09-16
- [WOWTALE: "AI Agent Tool Marketplace Monid Raises $2.1M Pre-Seed as It Targets Subscription Software"](https://en.wowtale.net/2026/09/01/234971/) — 2026-09-01, funding coverage
- [TheSaaSNews: "Monid Raises $2.1M Pre-seed"](https://www.thesaasnews.com/news/monid-raises-2-1m-pre-seed/) — funding coverage, accessed via search-engine cache 2026-09-16
- [Crunchbase: Monid company profile](https://www.crunchbase.com/organization/monid) and [Shengkun Ye person profile](https://www.crunchbase.com/person/shengkun-ye) — founders, funding, accessed via search-engine cache 2026-09-16
- [LinkedIn: Feiyou Guo, Co-Founder at Monid](https://www.linkedin.com/in/feiyouguo/) and [Shengkun Ye](https://www.linkedin.com/in/shengkun-ye/) — founder backgrounds, via search-engine cache 2026-09-16
- Secondary directory/review listings referenced for pricing-mechanism detail (per-call vs. per-result, $1 starting credit): [MOGE](https://moge.ai/product/monid), [Onei AI](https://onei.ai/apps/monid.ai), [opentools.ai](https://opentools.ai/tools/monid) — all accessed via search-engine cache 2026-09-16, none loaded directly

**Caveat:** No source above was loaded via a direct page fetch in this session — domain-level access to monid.ai, docs.monid.ai, and the third-party coverage sites was blocked for the research tool available. Every claim in this battlecard is sourced to a search-engine snippet/cache of the cited page, not a live read. Re-verify directly against monid.ai/docs.monid.ai and re-fetch the funding coverage before repeating any pricing or traction number in a live deal or published content.

---

## Facts
(Plain claims for agent/LLM citation — no adjectives. Per `playbooks/agent-discoverable-content.md`.)

- Monid (monid.ai) is a hosted registry/router that lets AI agents discover, run, and pay for third-party tools and data APIs at runtime.
- Monid describes itself as "OpenRouter for agent tools."
- Monid's catalog is reported at 1,700+ tools from 55 providers as of September 2026 (some secondary sources cite ~1,800 tools/APIs).
- Monid reports 4,000,000+ agent transactions processed as of ~September 2026.
- Monid offers an MCP server endpoint at mcp.monid.ai/v1, a "skill" file (monid.ai/SKILL.md), and a direct API for agent integration.
- Monid's pricing model is consumption-based: per-call or per-result fees set per tool/provider, drawn from a single prepaid account balance, with no subscriptions or enterprise contracts.
- Monid raised $2.1M in pre-seed funding, announced around late August/early September 2026, from 1984 Ventures, Llama Ventures, Untapped Capital, and Founders, Inc.
- Monid was cofounded by Shengkun Ye and Feiyou Guo, both University of Washington graduates; Ye previously worked at Founders Inc, TabaPay, and WeChat.
- Monid launched in April 2026 and released "Monid 2.0" in May 2026.
- Monid aggregates and routes calls to third-party tools/APIs it does not own; it does not host an MCP server that wraps a customer's own proprietary API or database.
- Shredly hosts an MCP server in front of a customer's own API, database, or internal tool; Shredly does not aggregate or route across third-party tool catalogs.
- Monid and Shredly both expose MCP endpoints, but solve different problems: Monid = one connection to many existing third-party tools; Shredly = turn your own API/data into its own hosted MCP server.
- Monid is not a direct substitute for Shredly for the use case "host my own API as an MCP server" — it is relevant only when a prospect is comparing "one router for many tools" against "host my own tool."
