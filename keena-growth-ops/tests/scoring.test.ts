import { test } from "node:test";
import assert from "node:assert/strict";
import { scoreCandidate, isoWeekKey } from "../lib/scoring.ts";
import type { RawCandidate } from "../lib/scoring.ts";

function fixture(overrides: Partial<RawCandidate> = {}): RawCandidate {
  return {
    sourceType: "rfp",
    organization: "Springfield General Hospital",
    title: "RFP: Electronic Health Record Conversion Services",
    url: "https://example.gov/rfp/12345",
    text: "Springfield General Hospital is soliciting proposals for EHR conversion and migration services.",
    location: "Springfield, IL",
    postedDate: "2026-09-01",
    deadline: "2026-10-15",
    ...overrides,
  };
}

test("scoreCandidate matches a known keyword to a Keena service line", () => {
  const lead = scoreCandidate(fixture(), "2026-W38", new Date("2026-09-16"));
  assert.ok(lead);
  assert.equal(lead!.serviceLine, "EHR Conversions");
  assert.equal(lead!.organization, "Springfield General Hospital");
  assert.equal(lead!.stage, "new");
  assert.equal(lead!.id, lead!.url);
});

test("scoreCandidate returns null for text with no ICP keyword match", () => {
  const lead = scoreCandidate(
    fixture({ text: "Springfield General Hospital seeks a parking lot resurfacing contractor." }),
    "2026-W38",
    new Date("2026-09-16")
  );
  assert.equal(lead, null);
});

test("scoreCandidate returns null for a candidate missing organization or url", () => {
  assert.equal(scoreCandidate(fixture({ organization: "" }), "2026-W38", new Date()), null);
  assert.equal(scoreCandidate(fixture({ url: "" }), "2026-W38", new Date()), null);
});

test("scoreCandidate excludes an RFP whose deadline has already passed", () => {
  const lead = scoreCandidate(
    fixture({ deadline: "2026-01-01" }),
    "2026-W38",
    new Date("2026-09-16")
  );
  assert.equal(lead, null);
});

test("scoreCandidate boosts fit for RFPs over job postings, and for recent postings", () => {
  const now = new Date("2026-09-16");
  const rfp = scoreCandidate(fixture({ postedDate: undefined, deadline: undefined }), "2026-W38", now)!;
  const job = scoreCandidate(
    fixture({ sourceType: "job_posting", postedDate: undefined, deadline: undefined }),
    "2026-W38",
    now
  )!;
  assert.ok(rfp.fit > job.fit);

  const recent = scoreCandidate(fixture({ postedDate: "2026-09-10", deadline: undefined }), "2026-W38", now)!;
  const stale = scoreCandidate(fixture({ postedDate: "2020-01-01", deadline: undefined }), "2026-W38", now)!;
  assert.ok(recent.fit > stale.fit);
});

test("isoWeekKey is stable within the same ISO week and formatted as YYYY-Www", () => {
  const monday = isoWeekKey(new Date("2026-09-14T09:00:00Z"));
  const wednesday = isoWeekKey(new Date("2026-09-16T09:00:00Z"));
  assert.equal(monday, wednesday);
  assert.match(monday, /^\d{4}-W\d{2}$/);
});
