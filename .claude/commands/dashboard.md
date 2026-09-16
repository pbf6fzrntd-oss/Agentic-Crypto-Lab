---
description: Regenerate and republish the visual pipeline dashboard
---
Run `python3 pipeline/crm.py dashboard` to regenerate `pipeline/dashboard.html` from the current `pipeline/contacts.csv`.

Then read `pipeline/dashboard_url.txt` for the existing artifact URL and republish it in place with the Artifact tool, passing that URL so it updates the same page rather than creating a new one: `Artifact({ file_path: "pipeline/dashboard.html", url: "<the URL from dashboard_url.txt>" })`.

Report the URL back once done.
