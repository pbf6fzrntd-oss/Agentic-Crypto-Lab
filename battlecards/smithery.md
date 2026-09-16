# Battlecard: Smithery (smithery.ai)

**Last checked:** 2026-09-16
**Last checked by:** competitive-intel agent

**Sourcing note (read before citing):** This environment's web-fetch tool could not directly load smithery.ai or several third-party review domains (blocked by network egress policy in this session) — all claims below come from web-search-indexed snippets of smithery.ai's own pricing/blog/docs pages (search results returned quoted/paraphrased text from those primary pages) and independent secondary sources (security researchers, review aggregators), each linked in Sources. Where secondary sources disagreed with each other, the disagreement is flagged rather than silently resolved. **Re-verify directly against smithery.ai/pricing and smithery.ai/blog before quoting exact prices in a live deal or public-facing comparison.**

## Summary

Smithery is an MCP (Model Context Protocol) registry and hosted gateway — tagline "Connect agents to services in minutes." Its core product is a public directory of thousands of already-built, mostly third-party MCP servers that developers can browse and install via CLI, plus a hosting/gateway layer for MCP servers that developers build and publish themselves. As of a blog post on smithery.ai (title "Important Update About Smithery Hosting"), Smithery discontinued free hosting: free-tier hosted servers remained live until March 1, 2026, and as of that cutover new deployments no longer go through on free plans — hosting now requires a paid plan, while registering an already-self-hosted "external server" in the registry (i.e., listing, not hosting) remains free.

Important structural distinction: Smithery hosts MCP servers *you build* (you write server code — TypeScript or Python, or publish an already-running server URL — and push it to GitHub for Smithery to build/deploy). It is not, as far as could be confirmed, a tool that auto-converts a raw REST API or database into an MCP server without you writing server code. (An "OpenAPI MCP Proxy" exists, but it is a third-party community server *listed in* Smithery's registry, not a first-party Smithery product capability — flagged as inferred/unconfirmed that Smithery itself offers a no-code API-to-MCP conversion feature.)

## Pricing

Confirmed (via search-indexed snippets of smithery.ai's own pricing/blog pages, not a direct fetch in this session — re-verify at smithery.ai/pricing):

- **Hobby — Free.** 50,000 RPCs/month, up to 3 namespaces, managed OAuth, persistent connections included. *(Source: smithery.ai/pricing via search snippet, checked 2026-09-16)*
- **Pay as You Go — $10/month.** 100,000 RPCs/month, up to 100 namespaces; usage beyond included RPCs billed at $0.10 per 1,000 RPCs. *(Source: smithery.ai/pricing via search snippet, checked 2026-09-16)*
- **Custom / Enterprise — pricing on request.** Everything in Pay as You Go, plus custom rate limits, an uptime SLA, and dedicated Slack support. *(Source: smithery.ai/pricing via search snippet, checked 2026-09-16)*

**Discrepancy flag:** at least one review-aggregator site (secondary source, not smithery.ai itself) described the paid entry tier as "Pro at $20/month" rather than "Pay as You Go at $10/month." This may reflect a stale/incorrect aggregator summary, an older price point, or a plan rename — could not resolve with certainty from this session. Treat the $10/month "Pay as You Go" figure as the better-supported reading (it appeared consistently with matching RPC/namespace details across multiple search results quoting the pricing page) but confirm directly before quoting either number externally.

**Hosting change (confirmed via smithery.ai's own blog post, per search snippet):** Free hosting discontinued. Previously-hosted free-tier servers stayed live until March 1, 2026. As of that date, new deployments no longer go through on free plans. To keep a listing on Smithery, a user must either upgrade to a paid plan to host on Smithery, or register an externally (self-)hosted server for free (free = free to *list*, not to *host*). Smithery's stated reason (per the blog post, as summarized in search results): architectural constraints in the old hosting made a quality patch impractical, so they are rebuilding hosting rather than continuing to patch it. *(Source: smithery.ai/blog/updates-to-our-hosting-plan via search snippet, checked 2026-09-16)*

**Inferred, not directly confirmed this session:** browsing the registry and using the CLI (`@smithery/cli`) to install/run existing third-party servers locally is still free — this is consistent with all secondary sources and Smithery's own docs describing free CLI usage, but no single source was fetched directly confirming "the CLI/registry remain free" as a standalone statement post-March-2026. Flagged as inferred.

## Features

- Public registry of MCP servers — count varies by source: Smithery's own materials (per search-indexed snippets) describe "over 6,000" to "over 7,000" listed servers; third-party trackers (Glama, LobeHub) report larger totals (tens of thousands) for the broader MCP ecosystem, of which Smithery is one registry among several. *(Sources: multiple, see below; checked 2026-09-16)*
- CLI (`@smithery/cli`, published on npm, requires Node 18+): install/uninstall/inspect/run servers from the registry, `dev` (hot-reload dev server), `build`, `playground` (interactive testing). *(Source: npm package page + smithery.ai/docs via search snippet)*
- Gateway/hosting layer manages OAuth, credentials, and persistent sessions for hosted servers, organized into "namespaces." *(Source: smithery.ai/docs via search snippet)*
- To publish your own server for Smithery to host: write the server (TypeScript or Python, exporting `createServer`/`configSchema` per Smithery's scaffold, or any language via `smithery mcp publish <url>` for an already-running server), add a `smithery.yaml` config at the repo root, push to GitHub, connect the repo to Smithery, and deploy from the server's "Deployments" tab. The published server gets a discoverable page at `smithery.ai/server/{name}`. *(Source: smithery.ai/docs, GitHub smithery-ai/cli, via search snippets, checked 2026-09-16)*
- Security history (independently confirmed via GitGuardian's own disclosure and multiple security-press outlets, not Smithery's own materials): a path-traversal vulnerability in Smithery's build infrastructure — improper validation of a `dockerBuildPath` parameter — was disclosed by GitGuardian researchers and, per GitGuardian's account, exposed API keys/auth tokens across roughly 3,000+ hosted servers; GitGuardian states Smithery remediated it within 48 hours of disclosure (disclosed June 13, 2025 per GitGuardian's post; picked up more widely in security press in October 2025). No report found of it having been exploited in the wild. *(Sources: GitGuardian blog, Security Boulevard, SC Media, cybersecuritynews.com — see Sources; checked 2026-09-16)*
- GitHub presence: the `smithery-ai/cli` repo shows on the order of ~265 stars per one search result — a data point on current mindshare, not a claim of obscurity or popularity either way. *(Source: search-indexed GitHub data, checked 2026-09-16, low confidence — recommend spot-checking the repo directly if this number matters to a claim)*

## Where Shredly wins

- **No code required to expose your own API/DB.** Shredly turns an existing REST API, database, or internal tool into a hosted MCP server without writing server code. Smithery's hosting model requires *you* to write the MCP server (a TypeScript/Python project with `smithery.yaml` and a `createServer` export, or an already-running server you point it at) and push it to GitHub before Smithery will build and host it — Smithery hosts servers you built; Shredly builds the server for you from your API/DB.
- **Simpler, flatter pricing for the SMB buyer.** Shredly: Free / $10 shared / $50 private, no per-RPC metering or namespace caps to reason about (per CLAUDE.md's confirmed tiers). Smithery's now-paid hosting is metered (RPCs/month, overage per 1,000 RPCs) and tiered by namespace count — more moving parts for a small team weighing cost before it's committed to the platform.
- **No disruptive tier change to explain.** Smithery's own free-hosting users had to migrate or upgrade around the March 1, 2026 cutover described on its own blog. A prospect evaluating "will my free plan get pulled later" has a concrete, sourced precedent to point to with Smithery; Shredly's tiers per CLAUDE.md have no such history to disclose as of this writing.
- **Built for the "I have one API, no MCP server yet" use case**, which is Shredly's core ICP (see CLAUDE.md). Smithery's core value proposition is discovery and reuse of servers *other people* already built; a company wanting to expose its own proprietary API isn't the primary use case the registry is built around.

## Where they win / honest gaps

- **Registry breadth.** Smithery lists on the order of thousands of existing third-party MCP servers (GitHub, Google Workspace, databases, productivity tools, etc. per third-party descriptions). Shredly does not operate a public registry/marketplace of pre-built servers at all. If the buyer's need is "find and connect to a server someone else already built" rather than "expose my own API," Smithery's registry is the more natural starting point — Shredly should not claim registry parity here.
- **Developer mindshare and ecosystem maturity.** Smithery has an established CLI, docs site, cookbook repo, and is referenced across numerous third-party MCP directories/review sites (Toolradar, aidevsetup, mcpize, TrueFoundry's registry roundup, etc.) as one of the go-to MCP registries. It has more existing public surface area than a newer, narrower platform like Shredly. This is a mindshare/brand-recognition gap, not a capability claim to concede on the core "turn my API into MCP" job.
- **Multi-language custom server support.** Smithery's build path supports publishing a server in any language you wrote it in (or an already-hosted-elsewhere server URL via `smithery mcp publish`). Teams that want to hand-write nontrivial custom MCP tool logic (not just wrap an existing API/DB schema) have more flexibility there than a schema-driven, no-code conversion model would offer.
- **Uncertain overlap on "no-code API conversion."** It could not be confirmed this session whether Smithery offers any first-party (not third-party/community) capability for auto-generating an MCP server from an OpenAPI spec without the user writing code — the one "OpenAPI MCP Proxy" found is a community-published server in the registry, not a documented core Smithery product feature. If Smithery ships or already has an undiscovered first-party no-code path, that would narrow this gap — flagged for re-verification, not asserted as absent.

## Facts

- Smithery (smithery.ai) is an MCP server registry and hosted gateway; tagline "Connect agents to services in minutes."
- Smithery's registry listed on the order of 6,000-7,000 MCP servers as of searches run 2026-09-16 (third-party trackers report larger totals for the broader MCP ecosystem across all registries combined).
- Smithery discontinued free hosting; previously free-hosted servers stayed live until March 1, 2026; new deployments stopped going through on free plans as of that date (source: smithery.ai/blog/updates-to-our-hosting-plan).
- Confirmed Smithery pricing tiers per search-indexed snippets of smithery.ai/pricing, checked 2026-09-16: Hobby (free, 50,000 RPCs/month, 3 namespaces); Pay as You Go ($10/month, 100,000 RPCs/month, 100 namespaces, $0.10 per 1,000 RPCs overage); Custom (pricing on request, adds custom rate limits, uptime SLA, dedicated Slack support).
- At least one secondary review site described Smithery's entry paid tier as "$20/month" rather than "$10/month" — unresolved discrepancy as of 2026-09-16; re-verify at smithery.ai/pricing before quoting a price externally.
- Registering an externally (self-)hosted MCP server in Smithery's registry (listing only, not hosting) remains free per the same blog post.
- To host a server on Smithery, the developer writes the server code (TypeScript/Python scaffold with `smithery.yaml`, or publishes an existing server URL) and pushes it to GitHub for Smithery to build/deploy; Smithery does not, as confirmed this session, offer a first-party no-code conversion from a raw REST API/database into an MCP server.
- Shredly converts an existing REST API, database, or internal tool into a hosted MCP server without the customer writing server code (per CLAUDE.md).
- Shredly's pricing tiers (per CLAUDE.md, confirm current numbers at shredly.io/pricing before quoting): Free (Google sign-in, shared environment, base limits); Shared $10/month (shared environment, expanded limits); Private $50/month (private/isolated MCP server, more granular controls).
- A path-traversal vulnerability in Smithery's build infrastructure (improper validation of a `dockerBuildPath` parameter) was disclosed by GitGuardian; GitGuardian states it exposed API keys/tokens across roughly 3,000+ hosted servers and was remediated within 48 hours of disclosure (disclosed June 13, 2025 per GitGuardian; covered more widely in security press in October 2025). No public report found of exploitation in the wild.

## Sources

- Smithery pricing page (smithery.ai/pricing) — accessed via search-indexed snippet, not direct fetch (egress-blocked in this session), checked 2026-09-16: https://smithery.ai/pricing
- Smithery blog, "Important Update About Smithery Hosting" — accessed via search-indexed snippet, checked 2026-09-16: https://smithery.ai/blog/updates-to-our-hosting-plan
- Smithery homepage — accessed via search-indexed snippet, checked 2026-09-16: https://smithery.ai/
- Smithery docs, CLI concept page — via search snippet: https://smithery.ai/docs/concepts/cli
- Smithery docs, TypeScript deployment guide — via search snippet: https://smithery.ai/docs/build/deployments/typescript
- Smithery docs, "Connect to MCPs" — via search snippet: https://smithery.ai/docs/use/connect
- `@smithery/cli` on npm — via search snippet: https://www.npmjs.com/package/@smithery/cli
- `smithery-ai/cli` on GitHub — via search snippet: https://github.com/smithery-ai/cli
- TrueFoundry, "Best MCP Registries in 2026" (secondary, registry size comparison): https://www.truefoundry.com/blog/best-mcp-registries
- GitGuardian blog, "From Path Traversal to Supply Chain Compromise: Breaking MCP Server Hosting" (primary security disclosure source): https://blog.gitguardian.com/breaking-mcp-server-hosting/
- Security Boulevard, republication of GitGuardian findings: https://securityboulevard.com/2025/10/from-path-traversal-to-supply-chain-compromise-breaking-mcp-server-hosting/
- SC Media, "Smithery.ai fixes path traversal flaw that exposed 3,000 MCP servers": https://www.scworld.com/news/smithery-ai-fixes-path-traversal-flaw-that-exposed-3000-mcp-servers
- cybersecuritynews.com, "Critical Vulnerability in MCP Server Platform Exposes 3,000+ Servers and Thousands of API Keys": https://cybersecuritynews.com/mcp-server-platform-vulnerability/
- Toolradar, Smithery review/pricing (secondary aggregator, source of the conflicting "$20/month" figure): https://toolradar.com/tools/smithery
- aidevsetup.com, Smithery MCP registry & gateway review (secondary): https://aidevsetup.com/mcp/smithery

**Not independently verified this session (secondary/review-aggregator claims only, lower confidence):** exact GitHub star count (~265, single source); precise current total registry server count (ranges 6,000-7,000 depending on source and date); whether Smithery has since shipped a first-party no-code API-to-MCP conversion feature.
