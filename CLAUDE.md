# Shredly.io — MCP Hosting Platform

This file loads automatically for every subagent in this project (unless a subagent sets `omitClaudeMd: true`), so it's the shared source of truth for positioning. Keep it current — every agent below reads it.

## What we do
Shredly turns your existing APIs, databases, and internal tools into hosted MCP (Model Context Protocol) servers — no infrastructure to deploy, no containers to run, no code to write. Sign in, grab a key, point any MCP-compatible client at it, and your data is live for AI agents in minutes.

## Ideal customer profile
- Eng teams (1-30 devs) building AI agent products or internal agent tooling who need to expose company data/APIs to an LLM
- Signal: has a REST API, database, or internal tool they want an agent to read/act on, but no MCP server for it yet
- Current alternative they're likely using: hand-rolling and self-hosting an MCP server, wiring custom tool-calling glue code, or not connecting agents to that data source at all

## Value proposition (one sentence)
Turn an API or database into a hosted MCP server in minutes — no infra, no ops, no code to deploy — and plug it straight into Claude, Cursor, Continue, Windsurf, or any MCP client.

## Pricing tiers (TODO — confirm with Shredly before using in outreach/content)
- Free / trial: Google sign-in, no credit card required, key issued in seconds (confirmed from site copy; exact free-tier limits not yet confirmed)
- Team: [not yet confirmed — get current pricing from shredly.io/pricing before quoting]
- Enterprise: [not yet confirmed]

> Agents: do not state specific prices, seat counts, or usage limits until this section is filled in with confirmed numbers. Until then, direct prospects to shredly.io for current pricing rather than guessing.

## Key differentiators vs. alternatives
- vs. self-hosting: no containers, servers, or on-call — Shredly runs and monitors uptime for you; you keep the API/database, we run the MCP layer in front of it
- vs. hand-coding an MCP server: no SDK to learn or server code to write — connect a REST API, database, or webhook and get a working MCP endpoint plus a key, not a codebase to maintain
- vs. general PaaS (Vercel/Railway/etc.): purpose-built for the MCP protocol — handles MCP auth, tool/resource schemas, and client compatibility (Claude Desktop, Cursor, Continue, Windsurf) out of the box, instead of generic app hosting you'd still have to wire up for MCP yourself

## Voice & tone
- Direct, technical, no hype. Show code/config, not adjectives.
- Never claim something isn't true to close a sale — the audience is developers who will check.

## Team of agents in this project
This project has specialist subagents in `.claude/agents/` for sales and marketing tasks: `content-seo`, `outbound-sdr`, `devrel-community`, `inbound-demo`, `customer-success`, `competitive-intel`. Delegate to the matching one when a task fits its description rather than doing the work in the main conversation — each keeps its output type isolated and consistent with this positioning doc.
