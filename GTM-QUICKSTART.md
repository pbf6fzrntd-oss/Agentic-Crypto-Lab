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
- `pipeline/contacts.csv` — the CRM's actual data (one row per company); `pipeline/crm.py` is the tool that reads/writes it; `pipeline/PIPELINE.md` is an auto-generated human-readable snapshot of the same data — edit the CSV via `crm.py`, not the snapshot
- `content/`, `outreach/`, `leads/`, `customer-comms/`, `community/`, `battlecards/` — each agent's isolated output folder
- `.claude/agents/` — the subagent definitions themselves
- `.claude/commands/` — the slash commands above

## The local CRM (`pipeline/crm.py`)
A small, dependency-free Python script — no network access, no email sending, just structured record-keeping so outbound/inbound/customer-success stay in sync instead of drifting across separate Markdown drafts.

```
python3 pipeline/crm.py find "acme"      # look up a company (also checks for dupes before adding)
python3 pipeline/crm.py add --company "Acme" --contact "Jane Doe" --email jane@acme.com \
  --role "Head of AI" --stage Prospecting --source outbound --owner outbound-sdr \
  --draft outreach/2026-09-16-acme.md --touch      # upsert; --touch advances the SMB cadence automatically
python3 pipeline/crm.py due               # who's overdue for a follow-up, oldest first
python3 pipeline/crm.py stats             # counts by stage, anything missing a next action
python3 pipeline/crm.py snapshot          # regenerate pipeline/PIPELINE.md from the CSV
```

`outbound-sdr`, `inbound-demo`, and `customer-success` all call this automatically as part of drafting — you generally don't need to run it by hand, but `/pipeline` and the commands above are there when you want to check status directly or fix a record.

## Keeping it current
- Pricing or positioning changed → edit `CLAUDE.md` (and `content/llms.txt` if it affects the public summary), everything downstream picks it up automatically.
- A competitor's pricing/features changed → `/battlecard <name>` to refresh; other agents defer to that file rather than re-researching.
- Run `/pipeline` (or `python3 pipeline/crm.py due`) periodically for overdue follow-ups — the agents log touches but don't chase follow-ups on a schedule themselves; you (or a scheduled Claude Code trigger, if you want to set one up) still have to ask for the next touch.

## Known gaps / next steps if you want more automation
- **No real email sending or external CRM sync.** This account has no Gmail/Outlook/HubSpot/Salesforce connector attached (checked at build time — only Google Drive is connected, and it's not enabled for GTM chats). Everything here produces Markdown drafts you copy-paste and send yourself, and `pipeline/contacts.csv` is local to this repo, not synced anywhere. If you connect an email or CRM connector later, ask to wire actual sending/syncing in — that should still confirm with you before each real send, since sending is visible to the recipient and hard to undo.
- Follow-up timing (touch 2/3 of a sequence) is tracked (`crm.py due` will tell you it's time) but not auto-triggered — you still run `/outreach` again yourself, or set up a scheduled check-in to remind you.
- `content/llms.txt` publishing to the live site is a manual step for whoever has shredly.io access — this repo only keeps the source copy current.
