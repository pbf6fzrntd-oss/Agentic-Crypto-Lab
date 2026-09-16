# Weekly search runbook

This is the exact procedure a Claude session follows once a week to refresh
`keena-growth-ops`'s lead pipeline. It exists because general web search
(RFPs, job postings — anywhere on the internet) can't be automated inside
the app's own server code the way an API call can: it needs a session with
WebSearch, not a plain HTTP client. Everything downstream of "here is a
list of real URLs" *is* plain, deterministic, tested code (`lib/ingest.ts`)
— this runbook only covers the discovery half.

Read this file in full before doing anything. If a step is ambiguous, err
towards including fewer, higher-confidence leads rather than more
speculative ones — a wrong lead costs someone at Keena real time.

## 0. Setup

```
cd keena-growth-ops
cat data/pipeline.json   # see what's already in the pipeline — never re-add a URL in here
```

## 1. Run these searches

Keena Healthcare Technology's real service lines (keenahealth.com): EHR
Conversions, KeenaArchive (legacy data archival/retention), InteleFiler /
Document Management, Interoperability (HL7/FHIR/interfaces), Epic
Consulting, Clinical Consulting, Advisory Consulting, Custom Development
(for healthcare IT vendors), Population Health, Disaster Recovery, Patient
Engagement, Financial Consulting (revenue cycle/claims), Workflow
Efficiency.

Run a WebSearch for each line below (adjust wording if a search returns
nothing useful — the goal is real, current, named-organization results,
not exhaustiveness). Use the current date to bias towards recent postings.

**RFPs / open solicitations** (append the current year; prefer results from
`.gov` domains, hospital/health-system procurement pages, or a named
procurement portal like Bonfire/BidNet/PlanetBids over aggregator/blog
pages):
- `RFP "electronic health record" conversion OR migration hospital <year>`
- `RFP "legacy system" archival healthcare records retention <year>`
- `RFP "document management system" hospital health system <year>`
- `RFP "health information exchange" OR interoperability OR HL7 <year>`
- `RFP "population health" platform health system <year>`
- `RFP "revenue cycle" OR "claims processing" hospital <year>`
- `site:sam.gov health IT OR EHR OR interoperability opportunity`

**Job postings** (as a buying-intent proxy — a hospital hiring for these
roles usually means an active initiative in that area):
- `hospital OR "health system" hiring "EHR conversion" OR "EHR migration" project manager`
- `"HL7 interface engineer" OR "interoperability analyst" hospital hiring <year>`
- `"Epic analyst" OR "Epic Bridges" hospital hiring <year>`
- `"clinical informatics consultant" OR CMIO hospital hiring <year>`
- `"document imaging" OR "health information management" specialist hospital hiring <year>`

## 2. Extract candidates

For each promising result, open it (WebFetch) if the domain isn't blocked;
otherwise use the search snippet. Only keep a result if you can fill in
**all** of:

- `organization` — the real, specific named organization (a hospital, health
  system, agency, or department — never an aggregator like "Indeed" or a
  generic "775 jobs" landing page)
- `title` — the RFP title or job title
- `url` — a real, direct link to that specific posting or notice
- `text` — enough of the title + summary/description to judge fit (a
  sentence or two is enough)
- `sourceType` — `"rfp"` or `"job_posting"`
- `postedDate` (ISO `YYYY-MM-DD`) if stated
- `deadline` (ISO `YYYY-MM-DD`) for RFPs, if stated — **check this against
  today's date yourself**; web search results are a stale index and
  frequently surface RFPs whose deadline already passed (this happened
  repeatedly in testing — IEHP, Sonoma County, and a VA RFI all showed up
  in search already closed). If you can't tell whether it's still open,
  include it anyway with the deadline field set — `lib/ingest.ts` will
  reject anything already past deadline, so it's safe to over-include here.

Skip anything you can't verify links back to a real, named organization.
A vague trend article ("hospitals are hiring more interoperability
analysts") is not a lead.

Aim for a diverse pool of 20-40 raw candidates across service lines so the
scoring/ranking step in `lib/ingest.ts` has enough to choose the best 15
(or fewer, if fewer than 15 real ones exist — an honestly small week is
correct, not a bug; never pad with weak matches to hit 15).

## 3. Write the candidates file

Write the array to `scripts/candidates.json` (gitignored — this is
scratch, not committed) as `RawCandidate[]` per `lib/scoring.ts`:

```json
[
  {
    "sourceType": "rfp",
    "organization": "Example County Department of Health Services",
    "title": "RFP: Electronic Health Records System",
    "url": "https://example.gov/rfp/12345",
    "text": "Example County is soliciting proposals for a cloud-based EHR system for its clinics.",
    "location": "Example County, CA",
    "postedDate": "2026-09-01",
    "deadline": "2026-10-30"
  }
]
```

## 4. Ingest

```
npm install   # only if node_modules isn't already present
npm run leads:ingest -- scripts/candidates.json
```

Read the printed summary. It tells you how many were added vs. skipped as
duplicate / out-of-ICP / expired / over this week's target. If `added` is
0 and you expected more, check whether your candidates' `url`s already
exist in `data/pipeline.json` (dedupe is by URL, forever — a lead is never
re-added even in a later week) or whether the `text` field actually
contains a matchable keyword (see `lib/keena-icp.ts`).

## 5. Commit and push

```
git add data/pipeline.json
git commit -m "chore(keena-growth-ops): weekly lead search — <ISO week>"
git push origin <the branch this Routine targets>
```

Do not commit `scripts/candidates.json` — it's scratch input, not the
source of truth (`data/pipeline.json` is).

## 6. Report back

In your final message, state how many leads were added this run, which
service lines they hit, and name anything you skipped that looked
promising but couldn't be verified (a person may want to check it by
hand). If zero were added, say so plainly along with why (e.g. "found 8
candidates, all already in the pipeline from last week's run").
