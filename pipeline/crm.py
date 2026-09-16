#!/usr/bin/env python3
"""Shredly GTM CRM — a small local CRM over pipeline/contacts.csv.

No external dependencies, no network access, no email sending. This just
keeps one structured record per company/contact so outbound, inbound, and
customer-success stay in sync instead of drifting across separate drafts.

Usage:
  python3 pipeline/crm.py add --company "Acme" [options] [--touch]
  python3 pipeline/crm.py due
  python3 pipeline/crm.py stats
  python3 pipeline/crm.py find "acme"
  python3 pipeline/crm.py snapshot
  python3 pipeline/crm.py dashboard   # writes pipeline/dashboard.html; publish it with the Artifact tool to view

Run with -h on any subcommand for its options.
"""
import argparse
import csv
import datetime
import json
import os
import sys

FIELDS = [
    "company", "contact_name", "contact_email", "persona_role",
    "stage", "source", "sequence_step",
    "first_touch_date", "last_touch_date",
    "next_action", "next_action_date",
    "owner_agent", "draft_path", "notes",
]

VALID_STAGES = [
    "Prospecting", "Contacted", "Replied", "Demo/Trial",
    "Customer", "Churned", "Closed-lost",
]

CLOSED_STAGES = {"Customer", "Churned", "Closed-lost"}

# SMB playbook cadence (see playbooks/SMB-PLAYBOOK.md): touch 1 -> wait
# ~4-5 days -> touch 2 -> wait ~1 week -> touch 3 (final).
CADENCE_DAYS = {1: 5, 2: 7}

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "contacts.csv")
SNAPSHOT_PATH = os.path.join(HERE, "PIPELINE.md")
DASHBOARD_TEMPLATE_PATH = os.path.join(HERE, "dashboard_template.html")
DASHBOARD_PATH = os.path.join(HERE, "dashboard.html")
LANDSCAPE_PATH = os.path.join(HERE, "partners_competitors.json")


def today():
    return datetime.date.today().isoformat()


def load_rows():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})


def find_row(rows, company):
    needle = company.strip().lower()
    for row in rows:
        if row["company"].strip().lower() == needle:
            return row
    return None


def cmd_add(args):
    rows = load_rows()
    row = find_row(rows, args.company)
    is_new = row is None
    if is_new:
        row = {k: "" for k in FIELDS}
        row["company"] = args.company
        row["sequence_step"] = "0"
        row["first_touch_date"] = today()
        rows.append(row)

    if args.contact:
        row["contact_name"] = args.contact
    if args.email:
        row["contact_email"] = args.email
    if args.role:
        row["persona_role"] = args.role
    if args.stage:
        if args.stage not in VALID_STAGES:
            sys.exit(f"error: --stage must be one of {VALID_STAGES}")
        row["stage"] = args.stage
    if args.source:
        row["source"] = args.source
    if args.owner:
        row["owner_agent"] = args.owner
    if args.draft:
        row["draft_path"] = args.draft
    if args.notes:
        existing = row.get("notes", "")
        row["notes"] = f"{existing} | {args.notes}" if existing else args.notes

    if args.touch:
        step = int(row.get("sequence_step") or 0) + 1
        row["sequence_step"] = str(step)
        row["last_touch_date"] = today()
        offset = CADENCE_DAYS.get(step)
        if offset:
            next_date = datetime.date.today() + datetime.timedelta(days=offset)
            row["next_action_date"] = next_date.isoformat()
            row["next_action"] = f"Send follow-up touch {step + 1}"
        else:
            row["next_action_date"] = ""
            row["next_action"] = "No more automated touches — decide manually (reply, close out, or move to nurture)"

    # Explicit --next-action/--next-date always win over auto-cadence above.
    if args.next_action:
        row["next_action"] = args.next_action
    if args.next_date:
        row["next_action_date"] = args.next_date

    if row["stage"] in CLOSED_STAGES:
        row["next_action"] = row["next_action"] or ""
        row["next_action_date"] = ""

    save_rows(rows)
    verb = "Added" if is_new else "Updated"
    print(f"{verb} {row['company']} — stage={row['stage'] or '(unset)'}, "
          f"next_action_date={row['next_action_date'] or '(none)'}")


def cmd_due(args):
    rows = load_rows()
    today_str = today()
    due = [
        r for r in rows
        if r.get("stage") not in CLOSED_STAGES
        and r.get("next_action_date")
        and r["next_action_date"] <= today_str
    ]
    due.sort(key=lambda r: r["next_action_date"])
    if not due:
        print("Nothing due.")
        return
    for r in due:
        print(f"{r['next_action_date']}  {r['company']:<24} {r['stage']:<12} "
              f"{r['next_action']}")


def cmd_stats(args):
    rows = load_rows()
    if not rows:
        print("No contacts yet.")
        return
    counts = {}
    for r in rows:
        counts[r.get("stage") or "(unset)"] = counts.get(r.get("stage") or "(unset)", 0) + 1
    print(f"Total: {len(rows)}")
    for stage in VALID_STAGES:
        if stage in counts:
            print(f"  {stage:<14} {counts[stage]}")
    stale = [
        r for r in rows
        if r.get("stage") not in CLOSED_STAGES and not r.get("next_action_date")
    ]
    if stale:
        print(f"No next action set: {', '.join(r['company'] for r in stale)}")


def cmd_find(args):
    rows = load_rows()
    needle = args.query.strip().lower()
    matches = [r for r in rows if needle in r["company"].strip().lower()]
    if not matches:
        print("No match.")
        return
    for r in matches:
        print(r)


def cmd_snapshot(args):
    rows = load_rows()
    stage_order = {s: i for i, s in enumerate(VALID_STAGES)}
    rows.sort(key=lambda r: (stage_order.get(r.get("stage"), 99), r.get("next_action_date") or "9999-99-99"))

    lines = [
        "# Shredly GTM Pipeline",
        "",
        "Auto-generated from `pipeline/contacts.csv` by `python3 pipeline/crm.py snapshot`. "
        "Do not hand-edit this file — edit contacts via `pipeline/crm.py add ...` "
        "(or, for agents without shell access, `pipeline/contacts.csv` directly) and re-run snapshot.",
        "",
        "| Company | Contact | Stage | Source | Last Touch | Next Action | Next Action Date | Owner | Draft |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| _(no contacts yet)_ | | | | | | | | |")
    for r in rows:
        lines.append(
            f"| {r['company']} | {r.get('contact_name','')} | {r.get('stage','')} | "
            f"{r.get('source','')} | {r.get('last_touch_date','')} | {r.get('next_action','')} | "
            f"{r.get('next_action_date','')} | {r.get('owner_agent','')} | {r.get('draft_path','')} |"
        )
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {SNAPSHOT_PATH} ({len(rows)} contacts)")


def cmd_dashboard(args):
    rows = load_rows()
    if os.path.exists(LANDSCAPE_PATH):
        with open(LANDSCAPE_PATH, encoding="utf-8") as f:
            landscape = json.load(f)
    else:
        landscape = {"competitors": [], "partners": [], "note": ""}
    with open(DASHBOARD_TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = (template
            .replace("__PIPELINE_DATA__", json.dumps(rows))
            .replace("__LANDSCAPE_DATA__", json.dumps(landscape))
            .replace("__GENERATED_AT__", generated_at))
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {DASHBOARD_PATH} ({len(rows)} contacts, "
          f"{len(landscape.get('competitors', []))} competitors, {len(landscape.get('partners', []))} partners). "
          f"Publish/update it with the Artifact tool to view it as a page.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new contact or update an existing one (upsert by company name)")
    p_add.add_argument("--company", required=True)
    p_add.add_argument("--contact", help="Contact person's name")
    p_add.add_argument("--email", help="Contact person's email")
    p_add.add_argument("--role", help="Persona/role, e.g. 'Head of AI'")
    p_add.add_argument("--stage", choices=VALID_STAGES)
    p_add.add_argument("--source", choices=["outbound", "inbound", "community", "referral"])
    p_add.add_argument("--owner", help="Owning agent, e.g. outbound-sdr")
    p_add.add_argument("--draft", help="Path to the drafted message, e.g. outreach/2026-09-16-acme.md")
    p_add.add_argument("--notes", help="Note to append (kept, not overwritten)")
    p_add.add_argument("--touch", action="store_true", help="Record a sequence touch now; auto-sets last_touch_date and the next cadence step's next_action/date per playbooks/SMB-PLAYBOOK.md")
    p_add.add_argument("--next-action", help="Explicit next action text (overrides auto-cadence)")
    p_add.add_argument("--next-date", help="Explicit next action date YYYY-MM-DD (overrides auto-cadence)")
    p_add.set_defaults(func=cmd_add)

    p_due = sub.add_parser("due", help="List contacts whose next action is due today or overdue")
    p_due.set_defaults(func=cmd_due)

    p_stats = sub.add_parser("stats", help="Show counts by stage and anything missing a next action")
    p_stats.set_defaults(func=cmd_stats)

    p_find = sub.add_parser("find", help="Search contacts by company name substring (use before adding, to dedupe)")
    p_find.add_argument("query")
    p_find.set_defaults(func=cmd_find)

    p_snap = sub.add_parser("snapshot", help="Regenerate pipeline/PIPELINE.md from contacts.csv")
    p_snap.set_defaults(func=cmd_snapshot)

    p_dash = sub.add_parser("dashboard", help="Regenerate pipeline/dashboard.html from contacts.csv (publish it with the Artifact tool to view)")
    p_dash.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
