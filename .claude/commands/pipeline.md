---
description: Show current GTM pipeline status
argument-hint: (optional) filter, e.g. a company name or stage
---
Read `pipeline/PIPELINE.md` and summarize the current pipeline: counts by stage, anything with no "Next Action" set, and anything that looks stale (no update in the "Last Touch" column relative to today). If an argument was given ($ARGUMENTS), filter to rows matching it instead of summarizing everything.
