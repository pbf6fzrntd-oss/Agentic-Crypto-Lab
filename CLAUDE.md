# Shredly.io — MCP Hosting Platform

This file loads automatically for every subagent in this project (unless a subagent sets `omitClaudeMd: true`), so it's the shared source of truth for positioning. Keep it current — every agent below reads it.

## What we do
Shredly turns your existing APIs, databases, and internal tools into hosted MCP (Model Context Protocol) servers — no infrastructure to deploy, no containers to run, no code to write. Sign in, grab a key, point any MCP-compatible client at it, and your data is live for AI agents in minutes.

## Ideal customer profile
- **Company size: SMB.** Small and medium-size businesses — roughly 1-200 people, not enterprise. Budget-conscious, no procurement process, buys on a card.
- **Buyer persona: the AI-team lead.** The person who owns "make our product/data usable by agents" — Head of AI/ML, founding/lead AI engineer, the first hire doing agent tooling, or a generalist eng lead wearing that hat at a smaller company. Not a platform/infra team at a large org.
- Signal: has a REST API, database, or internal tool they want an agent to read/act on, but no MCP server for it yet; or is already experimenting with Claude/Cursor/agent tooling internally.
- Current alternative they're likely using: hand-rolling and self-hosting an MCP server, wiring custom tool-calling glue code, or not connecting agents to that data source at all.
- Buying motion is self-serve/PLG, not enterprise sales: default every touch (outbound, inbound, content CTAs) to "sign in and try it" over "book a call." See `playbooks/SMB-PLAYBOOK.md` for the default sequence and tone.

## Value proposition (one sentence)
Turn an API or database into a hosted MCP server in minutes — no infra, no ops, no code to deploy — and plug it straight into Claude, Cursor, Continue, Windsurf, or any MCP client.

## GTM motion: agent-discoverable marketing
Alongside marketing to the human AI-team lead above, we also market to the AI agents doing tool research and procurement on that human's behalf — an agent evaluating "what do I recommend/use for MCP hosting" should be able to find and cite Shredly accurately. Concretely:
- Keep `content/llms.txt` current — it's the canonical machine-readable summary of what Shredly does, pricing, and how it compares, meant to be published at `shredly.io/llms.txt`.
- Every comparison/battlecard should include a clearly-labeled, terse "facts" block (plain claims, no adjectives) that an LLM can lift and cite directly, separate from the narrative prose around it.
- See `playbooks/agent-discoverable-content.md` for the full checklist (structured facts, FAQ-style headers, avoiding claims that only make sense to a human reader).
- This is a supplement to, not a replacement for, marketing to the human buyer persona above — content should serve both a human skimming it and an agent parsing it.

## Pricing tiers
- Free: Google sign-in, no credit card required, key issued in seconds. Runs on the shared MCP environment with base data/call limits.
- Shared ($10/month): the shared MCP environment with expanded data/call limits beyond the free tier.
- Private ($50/month): a private MCP server (not shared) with more granular controls (access, limits, isolation) than the shared environment.

> Agents: these three tiers are confirmed. Still verify current numbers at shredly.io/pricing before quoting in a live deal in case they've since changed, and never invent tiers, limits, or discounts beyond what's listed here.

## Key differentiators vs. alternatives
- vs. self-hosting: no containers, servers, or on-call — Shredly runs and monitors uptime for you; you keep the API/database, we run the MCP layer in front of it
- vs. hand-coding an MCP server: no SDK to learn or server code to write — connect a REST API, database, or webhook and get a working MCP endpoint plus a key, not a codebase to maintain
- vs. general PaaS (Vercel/Railway/etc.): purpose-built for the MCP protocol — handles MCP auth, tool/resource schemas, and client compatibility (Claude Desktop, Cursor, Continue, Windsurf) out of the box, instead of generic app hosting you'd still have to wire up for MCP yourself

## Voice & tone
- Direct, technical, no hype. Show code/config, not adjectives.
- Never claim something isn't true to close a sale — the audience is developers who will check.

## Team of agents in this project
This project has specialist subagents in `.claude/agents/` for sales and marketing tasks: `content-seo`, `outbound-sdr`, `devrel-community`, `inbound-demo`, `customer-success`, `competitive-intel`. Delegate to the matching one when a task fits its description rather than doing the work in the main conversation — each keeps its output type isolated and consistent with this positioning doc. Slash commands in `.claude/commands/` wrap the common ones — see `GTM-QUICKSTART.md`.

## Pipeline tracking (local CRM)
`pipeline/contacts.csv` is the single structured record of every prospect/customer, driven through `pipeline/crm.py` (stdlib-only Python, no network access — it does not send anything). Any agent that touches a named prospect or customer (`outbound-sdr`, `inbound-demo`, `customer-success`) logs/updates that company's record via `python3 pipeline/crm.py add ...` in the same turn it writes its draft, and checks `python3 pipeline/crm.py find "<company>"` first to avoid duplicate records. `pipeline/PIPELINE.md` is a generated human-readable snapshot (`crm.py snapshot`) — don't hand-edit it. Use `/pipeline` (or `python3 pipeline/crm.py stats` / `due`) to see overall status and what's due for follow-up.

This is a local record-keeping tool only — there is no connected email/CRM provider in this workspace, so nothing here sends email or syncs to an external CRM. Drafts remain Markdown files you send yourself; see `GTM-QUICKSTART.md` if you want to wire in an actual send/sync integration later.

## Playbooks
`playbooks/SMB-PLAYBOOK.md` and `playbooks/agent-discoverable-content.md` contain the default sequences, tone, and checklists for the SMB motion and the agent-discoverable content initiative described above. Agents producing outreach, content, or lead replies should follow them by default rather than improvising a generic B2B/enterprise motion.
