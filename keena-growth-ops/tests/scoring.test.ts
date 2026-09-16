import { test } from "node:test";
import assert from "node:assert/strict";
import { scoreNpiRecord, isoWeekKey } from "../lib/scoring.ts";
import type { NpiResult } from "../lib/npi.ts";

function fixture(overrides: Partial<NpiResult> = {}): NpiResult {
  return {
    number: "1234567890",
    enumeration_type: "NPI-2",
    basic: {
      organization_name: "Test General Hospital",
      enumeration_date: "01/01/2010",
      last_updated: "01/01/2010",
      status: "A",
    },
    addresses: [{ address_1: "1 Main St", city: "Springfield", state: "IL", postal_code: "62701" }],
    taxonomies: [{ desc: "General Acute Care Hospital", primary: true }],
    ...overrides,
  };
}

test("scoreNpiRecord matches a known taxonomy to a Keena service line", () => {
  const lead = scoreNpiRecord(fixture(), "2026-W10", new Date("2026-06-01"));
  assert.ok(lead);
  assert.equal(lead!.focus, "EHR Conversions");
  assert.equal(lead!.company, "Test General Hospital");
  assert.equal(lead!.state, "IL");
  assert.equal(lead!.stage, "new");
});

test("scoreNpiRecord returns null for an out-of-ICP taxonomy", () => {
  const lead = scoreNpiRecord(
    fixture({ taxonomies: [{ desc: "Individual Massage Therapist", primary: true }] }),
    "2026-W10",
    new Date("2026-06-01")
  );
  assert.equal(lead, null);
});

test("scoreNpiRecord returns null when the org has no name", () => {
  const lead = scoreNpiRecord(
    fixture({ basic: { organization_name: undefined } }),
    "2026-W10",
    new Date("2026-06-01")
  );
  assert.equal(lead, null);
});

test("scoreNpiRecord flags a recently updated record as a signal lead with a fit boost", () => {
  const now = new Date("2026-06-15");
  const recent = fixture({ basic: { organization_name: "Recent Health System", last_updated: "06/01/2026" } });
  const stale = fixture({ basic: { organization_name: "Stale Health System", last_updated: "01/01/2010" } });

  const recentLead = scoreNpiRecord(recent, "2026-W24", now)!;
  const staleLead = scoreNpiRecord(stale, "2026-W24", now)!;

  assert.equal(recentLead.discovery, "signal");
  assert.equal(staleLead.discovery, "prospect");
  assert.ok(recentLead.fit > staleLead.fit);
});

test("isoWeekKey is stable within the same ISO week and formatted as YYYY-Www", () => {
  const monday = isoWeekKey(new Date("2026-09-14T09:00:00Z"));
  const wednesday = isoWeekKey(new Date("2026-09-16T09:00:00Z"));
  assert.equal(monday, wednesday);
  assert.match(monday, /^\d{4}-W\d{2}$/);
});
