# Battlecard: mcphosting.io

**Last checked: 2026-09-16**

> **Research note on sourcing — read before using this card.** Direct fetch access to `mcphosting.io`, `www.mcphosting.io`, `manufact.com`, `apigene.ai`, and `diyai.io` was blocked by this environment's network egress proxy during research (policy-level `EGRESS_BLOCKED`, not a transient error — not retried per proxy guidance). `mcphosting.io` also has no public docs site, CLI reference, or API reference to fall back on. Every claim below comes from search-engine-indexed excerpts — snippets that appear to be crawled directly from mcphosting.io's own single marketing page, plus a third-party comparison post on manufact.com (a competing MCP-infrastructure vendor, published ~August 2026) — not from a directly-loaded primary page. This is thinner sourcing than other Shredly battlecards and should be treated accordingly: re-attempt a direct fetch before quoting anything from this card in a live deal or publishing it externally, and do not cite a specific figure (pricing, limits) to a prospect as settled fact from this card alone.

## Summary

mcphosting.io is a free, zero-config serverless hosting/deployment platform for MCP servers that a developer has already written in Python (using the FastMCP framework) or Node.js. It connects to GitHub for CI/CD-style deploys ("push a commit, get a new build; open a PR, get a branch deployment"), provides built-in OAuth, and works with Claude, Cursor, ChatGPT, and other MCP clients. Based on everything found, it is best described as **"Vercel/Railway for MCP server code you write yourself,"** not a no-code API/database-to-MCP converter — it has effectively no public documentation, no published paid tier, and appears to be aimed at hobby/experimental projects rather than production use.

**Key question answered:** Does mcphosting.io require the customer to already have written MCP server code, or can it convert an existing API/database like Shredly does?
**Answer, based on available sourcing: it requires code.** Every description found describes it as hosting/deploying MCP server code written in Python (FastMCP) or Node.js and pushed via a connected GitHub repo, with optional starter templates to speed that up — not a feature that ingests an arbitrary existing REST API or database and auto-generates an MCP endpoint in front of it without code. No source found describes an API-import, database-connector, or no-code conversion feature. This is consistent across multiple independent search queries but is inferred from secondary/indexed sources, not confirmed by directly reading mcphosting.io's own page — flag as high-confidence inference, not a directly-quoted primary-source statement.

## Pricing

- **Free tier: $0/month**, described as free "indefinitely" / "for free" — serverless hosting for Python FastMCP and Node.js MCP servers. (Source: search-indexed excerpts of mcphosting.io homepage and manufact.com/blog/best-mcp-deployment-platforms, accessed 2026-09-16 — not independently loaded)
- **No published paid tier.** Multiple independent search passes, including a dedicated comparison article on manufact.com, explicitly note there is **no published paid pricing** for mcphosting.io as of the article's publication (~August 2026). Treat "it's entirely free" as accurate only for whatever the current free tier's limits are — those limits themselves are not disclosed anywhere found. (Source: manufact.com/blog/best-mcp-deployment-platforms, via search index, accessed 2026-09-16)
- No usage limits, rate limits, storage caps, or overage terms were found anywhere — this is a genuine documentation gap on their side, not something we chose not to look for.

## Features

(All sourced from search-indexed excerpts of mcphosting.io's own homepage unless noted; not independently loaded — treat as inferred-from-primary rather than confirmed-by-direct-read.)

- Hosts MCP servers written in **Python using the FastMCP framework**, or in **Node.js**.
- **GitHub-connected deploys**: connect a repo (or start from a template); pushing a commit triggers a new build, opening a PR triggers a branch deployment.
- Marketed as **zero-config / no YAML** — "sub-second cold starts," serverless, no infrastructure for the customer to manage.
- **Built-in OAuth**, with an option to "bring your own identity provider" per one indexed excerpt (unconfirmed detail).
- Supports both **HTTP and stdio transport**, described as compatible with Claude Web, Claude Desktop, Cursor, ChatGPT, and "any MCP client."
- **MCP-aware analytics**: request/response pairs and tool-usage tracking, per manufact.com's comparison.
- One indexed excerpt also references a **self-hosting option via Docker images/deployment guides** for customers who want full control instead of the hosted free tier — unconfirmed against a directly-loaded page, noted here as a plausible but unverified secondary detail.
- **No evidence found** of: a paid/production tier, SLA or uptime commitment, compliance certifications (SOC 2, etc.), a CLI, an API reference, or a docs site of any kind. Manufact.com's comparison explicitly calls this out as disqualifying it for production use "until documentation exists."

## Where Shredly wins

- **No-code API/database → MCP conversion.** This is Shredly's core mechanism per `CLAUDE.md`: connect a REST API, database, or webhook and get a working MCP endpoint plus a key — no server code to write or maintain. mcphosting.io, on all available evidence, requires the customer to already write (or template-start) actual MCP server code in Python/FastMCP or Node.js and push it to GitHub. A prospect whose actual need is "I have an existing API/DB and no MCP server for it yet" — Shredly's stated ICP signal — has to write and maintain a codebase on mcphosting.io; on Shredly they don't.
- **No maintainable codebase to own.** Even with GitHub-connected deploys, mcphosting.io leaves the customer owning and maintaining an MCP server codebase (schema definitions, tool logic, dependency updates). Shredly's differentiator vs. hand-coding an MCP server (per `CLAUDE.md`) applies directly here.
- **Documentation and production-readiness.** By a competitor's own published assessment (manufact.com, August 2026), mcphosting.io has no docs site, no CLI/API reference, and no compliance information, and is explicitly recommended only for "hobby projects and experiments," not production. Shredly should be positioned as the option for teams that need something they can actually run a real workflow on, not just prototype with.
- **Clear, published pricing.** Shredly's three tiers ($0 free / $10 Shared / $50 Private) are public and simple. mcphosting.io has no published paid tier at all — a prospect evaluating it has no way to know what happens if/when they outgrow the free tier, or what "free" is actually bounded by.

## Where they win / honest gaps

- **Genuinely $0, no stated limits found, for hosting code you've already written.** If a prospect already has MCP server code in Python/FastMCP or Node.js and just wants free, zero-config hosting with GitHub CI/CD, mcphosting.io is a real, simpler-to-reach-for option for that narrow job — and it's free where Shredly's Shared/Private tiers are paid. Don't claim Shredly is free for anyone who already has server code and just needs hosting; that specific use case is what mcphosting.io targets.
- **GitHub-native deploy workflow.** Push-to-deploy and PR-branch-deploys are a specific, developer-familiar workflow that isn't confirmed as part of Shredly's flow one way or the other in `CLAUDE.md` — don't claim parity here without checking.
- **Framework flexibility for developers who want to write code.** For a developer who wants full control over MCP server logic (custom tool implementations, arbitrary business logic beyond a schema-mapped API/DB), a code-first platform like mcphosting.io is a legitimate fit that Shredly's connect-your-API model doesn't try to replace.
- **Honest framing for reps:** because mcphosting.io's sourcing is unusually thin, don't overstate the case against it either — we could not confirm it lacks an API/DB-conversion feature by reading their own docs (there are none), only infer this from consistent secondary descriptions. If a prospect says mcphosting.io does something not covered here, treat that as new information to re-verify, not something to dismiss.

## Facts

- mcphosting.io hosts MCP servers written in Python (FastMCP framework) or Node.js.
- mcphosting.io deploys via a connected GitHub repository; a push triggers a new build and a PR triggers a branch deployment.
- mcphosting.io's free tier is reported as $0/month with no disclosed usage limits found in available sourcing.
- mcphosting.io has no published paid pricing tier as of the sources checked (accessed September 16, 2026).
- mcphosting.io has no public documentation site, CLI reference, or API reference identified in this research.
- mcphosting.io requires the customer to already have, or write from a template, actual MCP server code; no API-import or database-to-MCP no-code conversion feature was found.
- mcphosting.io supports both HTTP and stdio MCP transport and lists compatibility with Claude, Cursor, and ChatGPT.
- Shredly's core product connects an existing customer API, database, or internal tool to a hosted MCP server without requiring the customer to write MCP server code (see `CLAUDE.md`).
- Shredly's pricing tiers are Free ($0, Google sign-in, no credit card), Shared ($10/month), and Private ($50/month) (see `CLAUDE.md` and `content/llms.txt`).

## Sources

- mcphosting.io homepage (`https://www.mcphosting.io/` and `https://mcphosting.io/`) — direct fetch attempted 2026-09-16, blocked by network egress proxy (`EGRESS_BLOCKED`) in this environment; all claims attributed to it are from search-engine-indexed excerpts of that page, accessed 2026-09-16.
- Manufact, "Best MCP Deployment Platforms 2026: 8 Compared," `https://manufact.com/blog/best-mcp-deployment-platforms` — direct fetch attempted 2026-09-16, blocked by network egress proxy; referenced via search-index summary only, accessed 2026-09-16. Note: Manufact is itself a competing MCP-infrastructure vendor, so treat its comparative framing (e.g., "rules it out for production use") as a competitor's opinion, even though the underlying documentation-gap observation is independently plausible given mcphosting.io has no docs site of its own to contradict it.
- Manufact, "MCP Platform Benchmark 2026: 8 Platforms Scored," `https://manufact.com/blog/mcp-deployment-platform-benchmark` — referenced via search-index summary only, accessed 2026-09-16, not directly loaded.
- Apigene, "Host MCP Server: The 2026 Deployment Guide," `https://apigene.ai/blog/host-mcp-server` — fetch blocked by network egress proxy; not used as a source beyond confirming the URL exists.
- diyai.io, "Best MCP Server Hosting in 2026," `https://diyai.io/ai-tools/hosting/best-mcp-server-hosting/` — fetch blocked by network egress proxy; not used as a source beyond confirming the URL exists.
- Internal: `/home/user/Agentic-Crypto-Lab/CLAUDE.md` (Shredly positioning, pricing, differentiators), `/home/user/Agentic-Crypto-Lab/content/llms.txt` (Shredly facts for consistency).

**Re-verification needed:** this is the thinnest-sourced battlecard in this set. Before citing it in a live deal, outbound message, or published comparison content, a human (or a future pass with unblocked egress) should directly load `mcphosting.io`'s homepage and any linked docs/GitHub repo to confirm: (1) whether a paid tier now exists, (2) actual free-tier limits, (3) whether any API/database-import feature has since been added, and (4) whether the "self-hosting via Docker" detail is real. Until then, treat every mcphosting.io claim in this card as "reported, not confirmed via primary source."
