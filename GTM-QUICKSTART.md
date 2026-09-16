# Shredly GTM Toolkit — Quickstart

## What this is
A set of Claude Code subagents for Shredly.io's go-to-market, tuned for the current motion: **SMB customers, self-serve pricing ($0/$10/$50 per month), buyer persona is the AI-team lead** (not enterprise procurement), plus a secondary track of **agent-discoverable content** so AI agents doing tool research recommend Shredly accurately.

`CLAUDE.md` is the shared source of truth every agent reads automatically — positioning, ICP, pricing, differentiators. Change it there, not per-agent, when positioning changes.

## Fastest way to use it: slash commands
| Command | Does |
|---|---|
| `/outreach <company or repo/signal>` | Draft SMB-style first-touch outbound (outbound-sdr) |
| `/lead <pasted inbound message>` | Qualify + reply to an inbound demo/signup (inbound-demo) |
| `/onboard <customer + situation>` | Onboarding, expansion, or save message (customer-success) |
| `/content <topic or "compare us to X">` | Blog/comparison/SEO content (content-seo) |
| `/community <thread URL or announcement topic>` | Community reply or post (devrel-community) |
| `/battlecard <competitor>` | Build/refresh a competitive battlecard (competitive-intel) |
| `/pipeline [filter]` | Summarize the current pipeline |

You can also just ask naturally ("draft a cold email to...") — Claude delegates to the matching agent automatically.

## Where things live
- `CLAUDE.md` — positioning, ICP, pricing, differentiators (edit this first when the business changes)
- `playbooks/SMB-PLAYBOOK.md` — default SMB sequences, tone, tier-fit guidance, objection handling
- `playbooks/agent-discoverable-content.md` — checklist for content that AI agents can parse/cite accurately
- `content/llms.txt` — canonical machine-readable summary of Shredly, meant to be published at shredly.io/llms.txt
- `pipeline/PIPELINE.md` — single tracker across outbound, inbound, and existing customers
- `content/`, `outreach/`, `leads/`, `customer-comms/`, `community/`, `battlecards/` — each agent's isolated output folder
- `.claude/agents/` — the subagent definitions themselves
- `.claude/commands/` — the slash commands above

## Keeping it current
- Pricing or positioning changed → edit `CLAUDE.md` (and `content/llms.txt` if it affects the public summary), everything downstream picks it up automatically.
- A competitor's pricing/features changed → `/battlecard <name>` to refresh; other agents defer to that file rather than re-researching.
- Check `/pipeline` periodically for stale rows (no "Next Action" set, or no touch in a while) — the agents log to it but don't currently chase follow-ups on a schedule themselves.

## Known gaps / next steps if you want more automation
- Follow-up timing (touch 2/3 of a sequence) is currently something you trigger manually via `/outreach` again — nothing here fires on a schedule yet.
- `content/llms.txt` publishing to the live site is a manual step for whoever has shredly.io access — this repo only keeps the source copy current.
- No CRM/email-send integration — everything here produces drafts in Markdown for you to send; ask if you want this wired into an actual email/CRM tool next.
