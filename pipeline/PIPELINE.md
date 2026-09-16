# Shredly GTM Pipeline

Single view across outbound, inbound, and existing customers. `outbound-sdr`, `inbound-demo`, and `customer-success` each add/update their own rows when they draft something for a named company/contact — append a new row rather than editing another agent's row, except to move a company between stages when a new event happens (e.g. inbound-demo marks a company "Customer" once outbound-sdr's lead converts).

## Columns
| Company | Contact | Stage | Source | Last Touch | Next Action | Owner Agent | Draft | Notes |
|---|---|---|---|---|---|---|---|---|

- **Stage**: `Prospecting` → `Contacted` → `Replied` → `Demo/Trial` → `Customer` → `Churned`/`Closed-lost`
- **Source**: `outbound`, `inbound`, `community`, `referral`
- **Draft**: relative path to the drafted message/reply in `outreach/`, `leads/`, or `customer-comms/`
- **Owner Agent**: which subagent last touched this row (`outbound-sdr`, `inbound-demo`, `customer-success`)

## Active pipeline

| Company | Contact | Stage | Source | Last Touch | Next Action | Owner Agent | Draft | Notes |
|---|---|---|---|---|---|---|---|---|
| _(no entries yet — agents append rows here as outreach/leads/customers are worked)_ | | | | | | | | |
