# Keena Growth Ops

A weekly, real-data sales pipeline for Keena Health. It surfaces up to
**15 real healthcare provider leads a week**, scored against Keena's
service lines, and tracks each one through a sales pipeline (New →
Contacted → Qualified → Meeting booked → Proposal sent → Won/Lost).

This started from a chat-exported UI mockup (hardcoded array of 15 fake
leads, a fake "run search" button that just waited 1.4s, `localStorage`
for state). Everything here replaces that with a real, working pipeline:
a real external data source, a real weekly cadence, and server-side
persistence.

## The real data feed

Every lead is a real organization pulled from the **CMS NPI Registry**
(`https://npiregistry.cms.hhs.gov`) — the official, free, keyless U.S.
government API of registered healthcare providers. No fabricated
companies, no paid lead-gen API key required.

- `lib/npi.ts` — the registry client (organizational/`NPI-2` records only).
- `lib/keena-icp.ts` — maps NUCC provider taxonomies (e.g. "General Acute
  Care Hospital", "Health Care System") to a Keena service line
  (EHR Conversions, Epic Consulting, Interoperability, ...) with a base
  fit score.
- `lib/scoring.ts` — turns one NPI record into a scored `Lead`. Records
  updated or newly enumerated in the registry recently are labeled
  **Signal** leads (something changed) and get a fit boost; everything
  else that still matches the ICP is a **Prospect** lead.
- `lib/leadgen.ts` — orchestrates a weekly run: queries a rotating subset
  of taxonomies (so coverage varies week to week), scores every result,
  never re-adds an NPI number already in the pipeline, and tops the
  current ISO week up to 15 new leads.
- `lib/store.ts` — a small JSON-file-backed pipeline store
  (`data/pipeline.json`). Every lead ever added is kept, tagged with the
  ISO week it was added in and its current pipeline stage.

### Known limitation — verify live network access once

This file was written in a sandbox whose organization egress policy
blocks outbound requests to `npiregistry.cms.hhs.gov` (confirmed via a
direct `curl`, and again via the app's own `/api/leads/refresh`, which
recorded a real `403 Forbidden` from the proxy for every taxonomy query).
The client is covered by unit tests with mocked `fetch` responses
(`tests/npi.test.ts`, `tests/leadgen.test.ts`) matching the NPI Registry
API v2.1 response shape, but it has **not yet been exercised against a
live response**. Run `npm run leads:refresh` once from an environment
with real network access (or trigger the GitHub Action manually) before
relying on the weekly schedule — the same discipline this repo's
crypto-research code applies to its own market-data fetch in
`../README.md`.

## Weekly cadence

- `npm run leads:refresh` (`scripts/weekly-refresh.ts`) runs the same
  orchestration outside the web server — commit-friendly for CI.
- `.github/workflows/keena-weekly-leads.yml` runs it every Monday and
  commits `data/pipeline.json` if it changed. Trigger it manually from
  the Actions tab (`workflow_dispatch`) to seed the pipeline immediately.
- The "Refresh this week" button in the UI calls `POST /api/leads/refresh`
  directly from the running server, for an on-demand top-up.

`data/pipeline.json` starts empty (`{"leads": [], "runs": []}`) — zero
leads is the correct starting point until the feed has actually been run
once with network access, not a bug.

## Persistence model — and its own limitation

`lib/store.ts` reads/writes `data/pipeline.json` on local disk. That's a
deliberate, simple choice for a single self-hosted Node process (a VM,
container, or `next start` on a normal server with persistent disk) or
for the GitHub-Actions-commits-the-data-file flow above. It is **not**
safe on a stateless serverless platform (Vercel, Cloudflare Workers,
etc.) where the filesystem resets between invocations — swap `lib/store.ts`
for a real database there (the module's surface is intentionally tiny:
`loadPipeline`/`savePipeline`/`updateLead`) before deploying to one.

## Swapping in a paid data provider later

If Keena later has an Apollo/Clearbit/ZoomInfo/Cognism API key, the swap
point is `lib/leadgen.ts` + `lib/npi.ts`: replace the NPI query with that
provider's client, keep returning the same shape `lib/scoring.ts` expects
(or adjust `scoreNpiRecord` accordingly), and the store, API routes, and
UI don't need to change.

## What's what

```
app/
  page.tsx              the pipeline UI: weekly queue, lead brief drawer,
                         pipeline-stage chips, CSV export, live refresh
  api/leads/route.ts             GET  — current pipeline + weekly stats
  api/leads/refresh/route.ts     POST — real fetch from the NPI Registry
  api/leads/[id]/route.ts        PATCH — update a lead's stage/notes
lib/
  npi.ts        real NPI Registry API client
  keena-icp.ts  taxonomy -> Keena service line fit map
  scoring.ts    NPI record -> scored Lead
  leadgen.ts    weekly orchestration (rotation, dedupe, 15/week cap)
  store.ts      JSON-file pipeline persistence
scripts/weekly-refresh.ts    standalone weekly entry point (npm run leads:refresh)
tests/                        mocked-fetch unit tests (no network, no cost)
.github/workflows/keena-weekly-leads.yml   scheduled weekly refresh + commit
```

## Run it

```
npm install
npm run dev              # http://localhost:3000
npm test                 # mocked unit tests, no network
npm run leads:refresh    # real fetch — needs outbound network to npiregistry.cms.hhs.gov
npm run build && npm start
```
