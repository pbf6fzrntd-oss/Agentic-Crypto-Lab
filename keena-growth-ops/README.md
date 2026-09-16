# Keena Growth Ops

A weekly, real-data sales pipeline for **Keena Healthcare Technology**
(keenahealth.com — EHR conversions, KeenaArchive, InteleFiler, clinical
consulting, and more). It surfaces up to **15 real open RFPs and job
postings a week**, matched to Keena's actual service lines, and tracks
each one through a sales pipeline (New → Contacted → Qualified → Meeting
booked → Proposal sent → Won/Lost).

This started from a chat-exported UI mockup (hardcoded array of 15 fake
leads, a fake "run search" button that just waited 1.4s, `localStorage`
for state). It first went through a version sourced from the CMS NPI
Registry; this version replaces that with **real open RFPs and job
postings** — a stronger, more direct buying-intent signal, per an explicit
ask to source leads that way instead.

## The real data feed — and why it looks different from a typical API integration

Every lead is a real RFP or job posting with a live source link — no
fabricated companies. But unlike the earlier NPI-based version, this data
can't be fetched by the app's own server on a schedule the way a plain API
call can: there is no free, unified, keyless API for "search all open
healthcare RFPs and job postings on the internet." The two real options
were a paid aggregator/lead-gen API (Apollo, ZoomInfo, GovTribe, HigherGov,
Adzuna, ...) or general web search — and web search is a tool available to
an interactive Claude session, not something a deployed Next.js server can
call itself.

So the pipeline is split into two halves:

1. **Agentic discovery (not code).** A Claude session runs a defined set of
   web searches every week, extracts real candidates (organization, title,
   URL, dates), and writes them as JSON. The exact procedure — including
   the actual search queries — is in **[`WEEKLY_SEARCH_RUNBOOK.md`](./WEEKLY_SEARCH_RUNBOOK.md)**.
2. **Deterministic ingestion (real, tested code).** `lib/ingest.ts` takes
   that JSON and does everything that can be tested without a network call:
   matches each candidate's text against Keena's real service lines
   (`lib/keena-icp.ts`), scores it, excludes any RFP whose deadline has
   already passed (search results are a stale index and this happens
   constantly — verified by hand while building this: RFPs from IEHP,
   Sonoma County, and a VA RFI all turned up in search already closed),
   dedupes against every URL ever added to the pipeline, and tops the
   current ISO week up to 15 new leads.

`scripts/ingest-candidates.ts` is the CLI entry point:
`npm run leads:ingest -- path/to/candidates.json`. `lib/store.ts` persists
the result to `data/pipeline.json`.

### Why this split matters for trust

Everything past step 1 is unit-tested with fixed input (`tests/*.test.ts`,
zero network calls, zero mocking needed — plain functions over plain data).
What *isn't* mechanically testable is whether a given week's web search
actually found the best real leads — that depends on judgment, same as a
human SDR researching accounts. The runbook is written to make that
judgment as consistent and low-risk as possible (verify deadlines, only
count named organizations, never scrape a site whose ToS forbids it).

## Weekly cadence

A scheduled Claude session (a Routine) follows `WEEKLY_SEARCH_RUNBOOK.md`
end to end: search, extract, ingest, commit `data/pipeline.json`, push. See
that file for the exact steps if you want to run a refresh by hand instead
of waiting for the schedule.

`data/pipeline.json` starts empty (`{"leads": [], "runs": []}`) — zero
leads is the correct starting point until a search run has actually
happened, not a bug.

## Persistence model — and its own limitation

`lib/store.ts` reads/writes `data/pipeline.json` on local disk. That's fine
for a single self-hosted Node process or for the commit-the-data-file flow
above, but **not** safe on a stateless serverless platform (Vercel,
Cloudflare Workers) where the filesystem resets between invocations — swap
`lib/store.ts` for a real database there. The module's surface is
intentionally tiny (`loadPipeline`/`savePipeline`/`updateLead`) to make
that swap contained.

## What's what

```
WEEKLY_SEARCH_RUNBOOK.md      the exact weekly procedure a Claude session follows
app/
  page.tsx                      pipeline UI: weekly queue, lead brief drawer with a
                                 live source link, pipeline-stage chips, CSV export
  api/leads/route.ts             GET  — current pipeline + weekly stats
  api/leads/[id]/route.ts        PATCH — update a lead's stage/notes
lib/
  scoring.ts    RawCandidate -> scored Lead (keyword match, expiry check, recency)
  keena-icp.ts  keyword -> real Keena service line map
  ingest.ts     weekly orchestration (dedupe by URL, 15/week cap, persistence)
  store.ts      JSON-file pipeline persistence
scripts/ingest-candidates.ts   CLI: npm run leads:ingest -- candidates.json
tests/                          pure-function unit tests, no network, no mocking
```

## Run it

```
npm install
npm run dev              # http://localhost:3000
npm test                 # unit tests, no network
npm run leads:ingest -- scripts/candidates.json   # after following the runbook
npm run build && npm start
```
