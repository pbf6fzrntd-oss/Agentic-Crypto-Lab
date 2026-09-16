# Battlecard: Glama (glama.ai)

**Last checked:** 2026-09-16
**Category:** MCP registry + inspector + gateway, with one-click hosting of MCP servers

> Verification note: glama.ai and third-party competitor pages (mcpize.com, composio.dev) were unreachable directly from this research environment (network egress blocked). All claims below come from live web search results whose snippets are attributed to glama.ai's own pages (homepage, /pricing, /mcp/hosting, /mcp/gateway, /mcp/servers), or from a GitHub mirror repo describing Glama, accessed 2026-09-16. Treat anything not explicitly marked "confirmed via direct fetch" as **search-snippet-sourced, not directly rendered** — a slightly weaker form of primary-source confirmation than fetching the page myself, but still first-party where the URL is glama.ai. Re-verify with a direct fetch when this environment's access allows it.

## Summary

Glama is an MCP server registry, inspector, and gateway that also offers one-click hosted deployment of MCP servers (open-source or your own, via GitHub repo/Dockerfile/npm/PyPI). It combines three things Shredly does not: (1) a public discovery directory of tens of thousands of third-party MCP servers, (2) an AI Gateway that unifies access to multiple LLM providers (OpenAI, Anthropic, Google, DeepSeek, Mistral, xAI), and (3) hosted MCP server deployment with per-tool access control, managed OAuth, and usage analytics. It is a much broader platform than a pure "turn my API into an MCP server" hosting product.

## Pricing

Source: search-engine snippets attributed to glama.ai/pricing, accessed 2026-09-16 (direct fetch blocked in this environment).

- **Free**: open-source MCP servers can be deployed and hosted for free. Paid tiers bundle "AI credits" (spent through Glama's AI Gateway) with hosted MCP server slots.
- **Starter — $9/month**: includes AI credits; reported as including 0 hosted MCP servers in this tier (i.e., registry/gateway access without dedicated hosting slots) — **unconfirmed detail, flagged as inferred from a secondary aggregation, not seen verbatim on glama.ai**.
- **Pro — $26/month**: 10 "fast" hosted MCP servers included, $3/month per additional dedicated server.
- **Business — $80/month**: 30 "fast" hosted MCP servers included, $2/month per additional dedicated server, 100k logs/month included ($3 per additional 100k logs), 180-day log retention, custom exports, priority support, request labeling.
- **Example overage cited in third-party summaries**: 50 dedicated servers on the Business plan ≈ $80 + (20 extra × $2) = $120/month. This is a derived calculation, not a quote from Glama's own page — confirm the per-server rate directly before repeating it in a live deal.
- Credit packs reportedly "stack" on any plan, including Free.

**Gap in my verification:** I could not directly render glama.ai/pricing to confirm exact current numbers, feature-by-feature tier breakdown, or whether these figures have changed since whatever date search engines last crawled the page. Do not quote exact Glama pricing to a prospect without a fresh direct check of glama.ai/pricing.

## Features

Source: search snippets attributed to glama.ai/, /mcp/hosting, /mcp/gateway, /mcp/faq, and a GitHub mirror (api-evangelist/glama, last modified 2026-05-23), accessed 2026-09-16.

- **MCP registry/directory**: large public index of open-source MCP servers with maintainer verification and quality/safety scoring. Self-reported count is volatile across sources and dates I found: ~12,610 (undated third-party listing), ~23,000 + ~4,000 hosted connectors (GitHub mirror snapshot dated 2026-05-23), ~37,800 (figure supplied in this task's brief, unverified against a primary source), and 88,155 (page title "Open-Source MCP Servers – 88,155 in the Glama Registry," the most recent search snippet as of 2026-09-16). **Flag: this number appears to be a live, fast-growing counter on Glama's own site rather than a stable figure — don't cite a specific count as current without checking the live page same-day.**
- **MCP Inspector**: ephemeral sandbox for testing MCP tools before/without deploying.
- **Hosted deployment**: connect a GitHub repo (built from source), or ship a Dockerfile, npm package, or PyPI module; configurable Node/Python versions, build steps, CMD args. One-click deploy of registry servers directly from their listing page ("Deploy Server").
- **Isolation**: each deployed server runs in its own Firecracker microVM with dedicated resources, persistent state, end-to-end encryption, and built-in observability (per glama.ai/mcp/hosting).
- **Gateway**: single control plane for MCP traffic with full JSON-RPC call logging, per-tool access control, managed OAuth credentials, usage analytics — applies both to servers you host on Glama and to third-party MCP endpoints you route through it.
- **AI Gateway (separate from MCP gateway)**: unified API access to OpenAI, Anthropic, Google, DeepSeek, Mistral, xAI models, paid for via the same credit pool as hosting.
- **Client support**: Claude Desktop, Claude Code, ChatGPT, Cursor, Windsurf, VS Code, Zed, JetBrains IDEs.
- **Visibility control**: deployments start private/access-gated; a single setting switch makes them public with a directory listing page.
- **Ops**: retry-on-failure restart policy, HTTP health checks, unhealthy-deployment flagging in the analytics dashboard, runtime log inspection.

## Where Shredly wins

- **Single-purpose simplicity for the SMB buyer.** Shredly's whole product is "point us at your API/database, get an MCP server" — no AI-model gateway, no public registry to configure around, no credit-based pricing model to reason about. For an SMB AI-team lead who wants one thing done fast, Shredly's surface area is smaller and the pricing (flat $0 / $10 / $50 tiers) is easier to reason about than Glama's credits + per-server-overage model.
- **Pricing predictability.** Shredly's three flat tiers have no metered/overage line items. Glama's model mixes a subscription, an AI-credit pool, per-additional-hosted-server charges, and per-100k-log-block charges — more moving parts to budget against, which matters more to a budget-conscious SMB buying on a card than to a team with procurement.
- **Not competing for registry attention.** Glama's hosting product is bundled inside a much larger discovery/marketplace platform aimed partly at consuming other people's MCP servers; Shredly's product is squarely about producing one from your own API/database with no distraction toward a public directory.
- **Positioning clarity vs. general PaaS is unambiguous** — Shredly's differentiators from CLAUDE.md (no infra to run, purpose-built MCP auth/schema handling) still apply against Glama's hosting layer, though Glama itself is also MCP-purpose-built, unlike Vercel/Railway (see gaps below).

## Where they win / honest gaps

- **Registry network effects.** Glama's public directory of (by its own recent count) tens of thousands of indexed MCP servers gives it a discovery/traffic advantage Shredly does not have — developers land on Glama looking for *any* MCP server, not just to host their own. Shredly has no public discovery surface today.
- **Enterprise logo claims.** Glama's homepage states "Trusted by 50,000+ Businesses and Professionals" and displays logos including Databricks, Accenture, Shopify, Cloudflare, Duolingo, Zomato, Zillow, Square, UiPath, and Neo4j (per search-snippet rendering of glama.ai's homepage, accessed 2026-09-16 — **not independently confirmed by direct fetch, and "50,000+ businesses and professionals" is Glama's own self-reported figure with no definition of what counts as a "business" — likely includes free-tier/registry users, not necessarily paying hosting customers**). Even discounted for marketing framing, this is a materially larger and more recognizable logo list than Shredly can currently show, and is a legitimate gap for an SMB buyer who weighs social proof.
- **Firecracker VM isolation and per-tool access control out of the box** are concrete, named security/ops features Glama documents for every hosted server — worth matching or clearly differentiating against in Shredly's own security messaging rather than ignoring.
- **Broader platform for teams that also want an AI-model gateway** (OpenAI/Anthropic/Google/etc. unified access) alongside MCP hosting — Shredly doesn't offer this and shouldn't try to; it's a different buying motive than "make our own API agent-usable."
- **Self-hosting existing open-source MCP servers is free on Glama** if the server is open-source — a real zero-cost option Shredly doesn't have an equivalent for (Shredly's free tier is for your own hosted server, not a marketplace of pre-built ones).

## Facts

- Glama offers a public MCP server registry/directory, an MCP Inspector, an MCP Gateway, and one-click hosted deployment of MCP servers.
- Glama's hosted MCP servers run in isolated Firecracker microVMs, per glama.ai/mcp/hosting (search-snippet sourced, not directly fetched, accessed 2026-09-16).
- Glama's gateway provides JSON-RPC call logging, per-tool access control, managed OAuth, and usage analytics.
- Glama pricing (search-snippet sourced from glama.ai/pricing, accessed 2026-09-16, not independently re-verified by direct fetch): Free for open-source servers; paid tiers reported at $9/month (Starter), $26/month (Pro, 10 hosted servers included, $3/extra server), and $80/month (Business, 30 hosted servers included, $2/extra server, 100k logs/month, 180-day retention).
- A commonly cited example: 50 dedicated servers on Glama's Business plan is calculated at approximately $120/month ($80 base + 20 extra servers × $2) — this is a derived example from third-party sources, not a verbatim Glama quote.
- Glama's self-reported registry size has ranged across sources/dates from roughly 12,610 to 88,155 indexed MCP servers; the figure changes frequently and should be re-checked live before citing a specific number.
- Glama's homepage states it is "Trusted by 50,000+ Businesses and Professionals" and lists logos including Databricks, Accenture, Shopify, Cloudflare, Duolingo, Zomato, Zillow, Square, UiPath, and Neo4j (self-reported, not independently verified by direct fetch of glama.ai; "businesses and professionals" is undefined and may include free/registry users, not only paying hosting customers).
- Glama also offers a separate "AI Gateway" for unified access to OpenAI, Anthropic, Google, DeepSeek, Mistral, and xAI models, billed from the same credit pool as hosting.
- Glama supports Claude Desktop, Claude Code, ChatGPT, Cursor, Windsurf, VS Code, Zed, and JetBrains IDE clients.
- Shredly's pricing is flat: Free (no card required), Shared $10/month, Private $50/month — no per-server overage or credit-metering model, per CLAUDE.md.
- Shredly does not currently operate a public MCP server discovery directory; Glama does.

## Sources

- Glama pricing page: https://glama.ai/pricing (content accessed via search-engine snippet on 2026-09-16; direct fetch blocked in this research environment — re-verify directly before quoting exact figures in a live deal)
- Glama homepage: https://glama.ai/ (search-snippet accessed 2026-09-16; direct fetch blocked)
- Glama MCP Hosting page: https://glama.ai/mcp/hosting (search-snippet accessed 2026-09-16; direct fetch blocked)
- Glama MCP Gateway page: https://glama.ai/mcp/gateway (search-snippet accessed 2026-09-16; direct fetch blocked)
- Glama MCP FAQ: https://glama.ai/mcp/faq (referenced via search, not directly read)
- Glama MCP servers registry index page ("Open-Source MCP Servers – 88,155 in the Glama Registry"): https://glama.ai/mcp/servers (search-snippet accessed 2026-09-16)
- GitHub mirror describing Glama's product/scale: https://github.com/api-evangelist/glama (directly fetched 2026-09-16; document itself dated created/modified 2026-05-23 — figures there, e.g. ~23,000 servers/~4,000 connectors, reflect that earlier date, not today)
- Third-party summary (secondary source, used only to cross-check pricing structure, not as primary confirmation): https://mcpize.com/alternatives/glama (accessed via search snippet 2026-09-16; direct fetch blocked)
- Third-party comparison (secondary source, referenced but not directly fetched — blocked): https://composio.dev/content/glama-alternatives

## Open verification items (re-check next update)

- Confirm exact current tier pricing and feature breakdown by direct fetch of glama.ai/pricing once network access permits.
- Confirm the "50,000+ businesses" figure and logo list by direct fetch of glama.ai homepage — this task's research relied on search-engine snippets, not a direct render.
- Confirm current registry server count on the live glama.ai/mcp/servers page at time of citation — it changes frequently.
- Confirm whether Starter ($9/mo) truly includes zero hosted MCP server slots, as this was inferred from a secondary aggregation rather than seen directly on Glama's own pricing page.
