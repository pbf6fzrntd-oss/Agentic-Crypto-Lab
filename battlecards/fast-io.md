# Battlecard: Fast.io

**Last checked: 2026-09-16**

> **Research note on sourcing:** Direct browser/fetch access to `fast.io`, `docs.fast.io`, and `g2.com` was blocked by this environment's network egress proxy during research, so claims below attributed to Fast.io's own site are drawn from search-engine-indexed excerpts of Fast.io's own pages (URL cited per claim) rather than a direct page load. Treat these as primary-source-derived but re-verify by loading the pages directly before quoting numbers in a live deal, and re-run this research the next time this battlecard is refreshed in case a direct fetch becomes possible.

## Summary

Fast.io is an AI-first cloud content/file-storage workspace — positioned as a modern alternative to Box, Dropbox, and Google Drive for teams that mix human and AI-agent collaboration on files — that also ships a hosted MCP server exposing its own storage/workspace product (files, shares, workflows, built-in RAG) as agent tools. It markets under a "serverless MCP" / "hosted MCP" banner and publishes a large volume of SEO/comparison content about the broader MCP-hosting market ("Best MCP Hosting Platforms," "Hosted MCP Services," "Best Serverless MCP Servers," etc.), which is why it surfaces in searches adjacent to Shredly's category even though the underlying product does something narrower and different from Shredly's core use case.

**Important, confirmed distinction:** Fast.io's MCP server gives agents tools to operate on files/data *stored inside Fast.io's own workspace product* (upload, search, share, RAG over your uploaded docs, etc.) — not a generic "point us at your existing REST API or database and we'll stand up an MCP server in front of it" product the way Shredly is. Its docs/marketing describe connecting *custom* MCP servers (e.g., a customer's own FastAPI-based MCP server) *alongside* a Fast.io workspace, and generic third-party tutorials about wrapping any API with MCP — but no confirmed Fast.io product feature that ingests an arbitrary customer API/database and hosts an MCP endpoint for it the way Shredly's core product does. This should be flagged to prospects as a category difference, not just a feature gap.

## Pricing

Sourced from search-indexed excerpts of `fast.io/pricing` and third-party listings (SaaSWorthy, G2); not independently loaded directly — verify before quoting.

- **Free tier**: $0/month, 50GB storage, 5,000 monthly credits, 5 workspaces, 50 shares, no credit card required, described as including full access to the MCP tool set. (Source: search-indexed fast.io content, accessed 2026-09-16)
- **Starter**: $29/month — 5 seats, 1TB storage. (Source: search-indexed fast.io pricing page, accessed 2026-09-16)
- **Business**: $99/month — 20 seats, 10TB storage; additional seats $1/user/month beyond the included allocation. A "Business Trial" (14 days, requires credit card per other tiers) was also referenced separately with 50GB storage and included credits — unclear if this is the same as the standing Business plan or a distinct trial SKU; **unconfirmed, flag as inferred**. (Source: search-indexed fast.io content, accessed 2026-09-16)
- **Growth**: $299/month — 50 seats, 50TB storage. (Source: search-indexed fast.io pricing page, accessed 2026-09-16)
- **Usage-based credits** (on top of/within plans): $10 per 100,000 credits (~$0.0001/credit). Credit costs cited: storage 100 credits/GB, bandwidth 212 credits/GB, AI tokens 1 credit/100 tokens, document ingestion 10 credits/page, video ingestion 5 credits/sec, image ingestion 5 credits/image, file conversions 25 credits/each. (Source: search-indexed fast.io pricing page, accessed 2026-09-16)
- Paid-tier trials are 14 days and require a credit card up front (contrast with Shredly's free tier, which does not). (Source: search-indexed fast.io content, accessed 2026-09-16)
- Model is usage/storage-based, not per-seat, per multiple sources including G2-adjacent summaries. (Source: search-indexed content referencing g2.com/products/fast-io0-fast-io, accessed 2026-09-16 — G2 page itself not directly loaded)

## Features

- MCP server access is available across the free and paid tiers; described as "serverless" — no infra for the customer to run, pre-warmed endpoint, managed auth/security/updates. (Source: search-indexed fast.io content, accessed 2026-09-16)
- **Tool count is inconsistent across Fast.io's own published pages**: some Fast.io pages/snippets say the MCP server exposes **"19 consolidated tools"**; others say **"251 tools" / "251+ tools"** covering "every UI capability as agent actions." Both figures appear on what are represented as Fast.io's own resource pages in search results. **This is a confirmed contradiction in their own marketing, not a Shredly inference** — we could not resolve which figure is current by directly loading the page. Do not repeat either number to a prospect as settled fact; say "Fast.io's own materials disagree on this (19 vs. 251+) as of Sept 2026" if it comes up. (Sources: multiple search-indexed fast.io resource pages, accessed 2026-09-16, URLs including fast.io/resources/fastio-mcp-server-integration-developers/, fast.io/resources/hosted-mcp/, fast.io/resources/mcp-server-comparison/)
- Tool categories described: file CRUD/storage, workspace management, sharing/permissions, URL imports, webhooks, AI chat, comments, workflow tasks, ownership transfer, and built-in RAG ("Intelligence Mode"). (Source: search-indexed fast.io content, accessed 2026-09-16)
- Built-in RAG ("Intelligence Mode"): files uploaded to a Fast.io workspace are automatically indexed for semantic search; agents can do Q&A with citations without wiring a separate vector database. This is what "RAG workspaces" refers to — RAG over files *you upload into Fast.io's own storage*, not a general-purpose RAG-over-arbitrary-data-source offering. (Source: search-indexed fast.io content, accessed 2026-09-16)
- Access methods beyond MCP: web UI, native Mac desktop app, CLI (npm), REST API. (Source: search-indexed content, accessed 2026-09-16)
- Framework integration claims (LangChain, CrewAI, OpenAI Swarm, AutoGen, Semantic Kernel, Haystack) via custom tools or MCP clients. (Source: search-indexed fast.io content, accessed 2026-09-16 — not independently verified against a framework)
- Publishes MCP deployment guides for third-party PaaS (Vercel, Railway, AWS Lambda, Render) that describe hosting *Fast.io's own* MCP client/connector on those platforms — this is content marketing/SEO material, not a Shredly-style "we host it for you" claim about arbitrary customer infra. (Source: search-indexed fast.io resource pages, accessed 2026-09-16)
- Free tier file size cap referenced at 1GB per file in one snippet; unconfirmed against a directly-loaded pricing page — **flag as inferred**. (Source: search-indexed fast.io content, accessed 2026-09-16)
- Fast.io's own comparison content ("Best MCP Hosting Platforms," "Hosted MCP Services," "MCP Server Comparison Guide") positions Fast.io within the general MCP-hosting category conversation, competing for the same search intent Shredly's content-seo targets — worth monitoring for how they frame Shredly or similar tools if named directly (not observed in this pass).

## Where Shredly wins

- **Core use case match**: Shredly's product is built to take a customer's *existing* API, database, or internal tool and stand up a hosted MCP server in front of *that data source*. Based on available sourcing, Fast.io's MCP server exposes Fast.io's own file-storage/workspace product — it is not confirmed to offer a generic "connect your API/database, get an MCP endpoint" flow. A prospect who wants to expose their own REST API or database to agents isn't well served by moving their data into Fast.io's storage product first.
- **No credit card, ever, for the free tier**: Shredly's free tier requires only Google sign-in. Fast.io's paid-tier trials require a credit card up front (its free tier itself reportedly does not, per sourcing above — verify before claiming this as a differentiator on the free tier specifically).
- **Simpler, purpose-built pricing**: Shredly's three flat tiers ($0 / $10 / $50) are simple to reason about. Fast.io's model layers seat counts, storage tiers, and a six-way usage-credit system (storage, bandwidth, AI tokens, ingestion by type, conversions) — more moving parts for a buyer to estimate cost against.
- **No ambiguity about what you get**: Fast.io's own materials disagree (19 vs. 251+ tools) on how many tools its MCP server exposes — a prospect evaluating tool surface area can't currently get a straight, consistent answer from Fast.io's own site as indexed. Shredly's tool/resource surface is scoped directly to the API or database the customer connects, not a fixed platform-tool catalog with internally inconsistent counts.
- **Purpose-built for exposing your own systems**: Shredly's differentiator vs. general PaaS (per `CLAUDE.md`) — handling MCP auth, tool/resource schemas, and client compatibility (Claude Desktop, Cursor, Continue, Windsurf) out of the box — is a fair contrast with Fast.io too, since Fast.io's MCP offering is scoped to its own storage product rather than being a general MCP hosting layer for any backend.

## Where they win / honest gaps

- **Built-in RAG over uploaded files, out of the box**: Fast.io's Intelligence Mode gives semantic search and cited Q&A over documents the moment they're uploaded, with no separate vector database to wire up. Shredly does not currently claim a built-in RAG/vector-search layer in `CLAUDE.md` — if a prospect's actual need is "let an agent semantically search a pile of documents," Fast.io's product is arguably a closer fit than Shredly's API/database-to-MCP model, and this should be said honestly rather than deflected.
- **Multi-surface product, not just MCP**: Fast.io gives a customer a full file-collaboration product (web UI, desktop app, CLI, REST API) with MCP as one access layer on top — useful if the buyer's actual need is "a Box/Dropbox alternative with agent access," not just "an MCP server for something we already run."
- **Established file/collaboration features**: video HLS streaming with adaptive bitrate, PDF/video engagement analytics in shared "data rooms," metadata extraction and templates, audit trails per G2-adjacent sourcing — these are mature product surface areas Shredly does not compete on and shouldn't claim to.
- **Content/SEO footprint**: Fast.io has published a large number of MCP-hosting comparison and how-to pages, giving it more surface area in searches for generic "MCP hosting platform" queries than Shredly currently has — worth noting for `content-seo` as a competitive signal, not a product gap.
- **Honest framing for reps**: because Fast.io's actual product (file storage + MCP access to that storage) differs from Shredly's (turn your own API/DB into an MCP server), the most honest comparison in a live conversation is often "different tool for a different job" rather than a head-to-head — don't force a false equivalence just because both use "MCP hosting" language in their marketing.

## Facts

- Fast.io is a cloud file-storage / content-collaboration platform marketed as an AI-first alternative to Box, Dropbox, and Google Drive.
- Fast.io offers an MCP server that exposes its own file storage, workspace, sharing, and RAG features as tools for AI agents.
- Fast.io's own published materials give two different tool counts for its MCP server: "19 consolidated tools" on some pages and "251" / "251+ tools" on others (as indexed, September 2026) — unresolved contradiction, not a confirmed single number.
- Fast.io's free tier is reported as $0/month, 50GB storage, 5,000 monthly credits, 5 workspaces, 50 shares, no credit card required (source: search-indexed fast.io pricing content, accessed September 16, 2026 — not independently loaded).
- Fast.io's paid tiers are reported as Starter $29/month (5 seats, 1TB), Business $99/month (20 seats, 10TB), Growth $299/month (50 seats, 50TB), plus usage-based credits for storage, bandwidth, AI tokens, and document/image/video ingestion (source: search-indexed fast.io pricing content, accessed September 16, 2026 — not independently loaded).
- Fast.io's paid-tier trials are reported as 14 days and require a credit card.
- Fast.io includes a built-in RAG feature ("Intelligence Mode") that auto-indexes uploaded files for semantic search and cited Q&A.
- Fast.io's MCP server is scoped to Fast.io's own storage/workspace product; no confirmed feature was found for hosting an MCP server in front of an arbitrary customer-owned REST API or database.
- Shredly's free tier requires only Google sign-in and no credit card; Shredly's paid tiers are Shared at $10/month and Private at $50/month (see `CLAUDE.md` and `content/llms.txt`).
- Shredly's core product connects an existing customer API, database, or internal tool to a hosted MCP server; Fast.io's core product is file storage with MCP as an access layer to that storage.

## Sources

- Fast.io homepage and product pages — attempted direct fetch on 2026-09-16, blocked by network egress proxy in this environment; claims sourced instead from search-engine-indexed excerpts of fast.io pages, including:
  - https://fast.io/resources/hosted-mcp/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/best-serverless-mcp-servers/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/best-mcp-hosting-platforms/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/fastio-mcp-server-integration-developers/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/mcp-server-comparison/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/integrate-fastio-mcp-server-agent-workflows/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/deploy-fastio-mcp-server-vercel/ (accessed via search index, 2026-09-16)
  - https://fast.io/resources/deploy-fastio-mcp-server-aws-lambda/ (accessed via search index, 2026-09-16)
  - https://fast.io/pricing/ and https://fastio-static-content.pages.dev/pricing (accessed via search index, 2026-09-16 — both blocked on direct fetch)
  - https://fast.io/resources/mcp-server-fastapi-python/ (accessed via search index, 2026-09-16)
  - https://fast.io/alternatives/box/, https://fast.io/alternatives/dropbox/ (accessed via search index, 2026-09-16)
- G2 (third-party review aggregator) — attempted direct fetch on 2026-09-16, blocked by network egress proxy; referenced only via search-engine summary of https://www.g2.com/products/fast-io0-fast-io/reviews and https://www.g2.com/products/fast-io0-fast-io/competitors/alternatives (accessed via search index, 2026-09-16).
- SaaSWorthy listing for Fast.io: https://www.saasworthy.com/product/fast-io (accessed via search index, 2026-09-16, not directly loaded).
- Internal: `/home/user/Agentic-Crypto-Lab/CLAUDE.md` (Shredly positioning, pricing, differentiators), `/home/user/Agentic-Crypto-Lab/content/llms.txt` (Shredly facts for consistency).

**Re-verification needed:** the network egress block on fast.io/g2.com in this environment prevented loading primary pages directly. Before this battlecard is cited in a live deal or published content, re-attempt a direct fetch of fast.io's pricing and MCP documentation pages (or have a human confirm via browser) to resolve the 19-vs-251 tool count discrepancy and confirm current pricing figures.
