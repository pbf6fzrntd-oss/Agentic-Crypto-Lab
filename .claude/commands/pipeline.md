---
description: Show current GTM pipeline status (stats, what's due, or look up a company)
argument-hint: (optional) a company name to look up, or "due" for follow-ups
---
Run `python3 pipeline/crm.py stats` and `python3 pipeline/crm.py due` and summarize the results in plain language: counts by stage, anything overdue on a next action, and anything missing a next action entirely.

If an argument was given ($ARGUMENTS), also run `python3 pipeline/crm.py find "$ARGUMENTS"` and report that company's full record instead of (or in addition to, if it's not a company name) the general summary.

After reporting, run `python3 pipeline/crm.py snapshot` to refresh `pipeline/PIPELINE.md` so the checked-in file matches the live data.
