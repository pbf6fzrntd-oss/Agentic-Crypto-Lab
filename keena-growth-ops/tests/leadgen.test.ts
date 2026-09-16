import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

function mockFetchByTaxonomy(recordsPerTaxonomy: number) {
  return (async (input: RequestInfo | URL) => {
    const url = new URL(String(input));
    const taxonomy = url.searchParams.get("taxonomy_description") ?? "unknown";
    const results = Array.from({ length: recordsPerTaxonomy }, (_, i) => ({
      number: `NPI-${taxonomy.replace(/\s+/g, "_")}-${i}`,
      enumeration_type: "NPI-2",
      basic: {
        organization_name: `${taxonomy} Org ${i}`,
        enumeration_date: "01/01/2015",
        last_updated: "01/01/2015",
      },
      addresses: [{ city: "Testville", state: "TX" }],
      taxonomies: [{ desc: taxonomy, primary: true }],
    }));
    return new Response(JSON.stringify({ result_count: results.length, results }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
}

test("refreshWeeklyLeads caps additions at 15/week and dedupes across weeks", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "keena-test-"));
  process.env.KEENA_DATA_FILE = path.join(dir, "pipeline.json");

  const originalFetch = globalThis.fetch;
  globalThis.fetch = mockFetchByTaxonomy(6); // 6 taxonomies queried/week * 6 records = 36 candidates

  try {
    const { refreshWeeklyLeads, WEEKLY_LEAD_TARGET } = await import("../lib/leadgen.ts");

    const weekOneDate = new Date("2026-06-01"); // Monday
    const first = await refreshWeeklyLeads(weekOneDate);
    assert.equal(first.run.added, WEEKLY_LEAD_TARGET);
    assert.equal(first.totalLeadsThisWeek, WEEKLY_LEAD_TARGET);

    // Same week again: already at target, nothing new should be added.
    const second = await refreshWeeklyLeads(weekOneDate);
    assert.equal(second.run.added, 0);
    assert.equal(second.totalLeadsThisWeek, WEEKLY_LEAD_TARGET);

    // A week later: the mocked feed re-offers the same 36 candidates (36 >
    // WEEKLY_LEAD_TARGET, so 21 were never persisted and never marked seen
    // last run). None of the 15 already IN the pipeline should ever be
    // re-added, even though they're still present in the mocked feed.
    const weekTwoDate = new Date(weekOneDate.getTime() + 7 * 24 * 60 * 60 * 1000);
    const third = await refreshWeeklyLeads(weekTwoDate);
    assert.equal(third.run.added, WEEKLY_LEAD_TARGET);
    const firstIds = new Set(first.addedLeads.map((l) => l.npiNumber));
    for (const lead of third.addedLeads) {
      assert.ok(!firstIds.has(lead.npiNumber), `week two re-added ${lead.npiNumber} from week one`);
    }

    const { loadPipeline } = await import("../lib/store.ts");
    const data = await loadPipeline();
    assert.equal(data.leads.length, WEEKLY_LEAD_TARGET * 2);
    assert.equal(new Set(data.leads.map((l) => l.npiNumber)).size, WEEKLY_LEAD_TARGET * 2);
  } finally {
    globalThis.fetch = originalFetch;
    delete process.env.KEENA_DATA_FILE;
    await rm(dir, { recursive: true, force: true });
  }
});

test("refreshWeeklyLeads records per-taxonomy fetch failures without aborting the run", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "keena-test-"));
  process.env.KEENA_DATA_FILE = path.join(dir, "pipeline.json");

  const originalFetch = globalThis.fetch;
  let call = 0;
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    call += 1;
    if (call === 1) return new Response("boom", { status: 500 });
    return mockFetchByTaxonomy(2)(input, {} as RequestInit);
  }) as typeof fetch;

  try {
    const { refreshWeeklyLeads } = await import("../lib/leadgen.ts");
    const result = await refreshWeeklyLeads(new Date("2027-01-04"));
    assert.ok(result.run.errors.length >= 1);
    assert.ok(result.run.added > 0, "later taxonomies should still contribute leads");
  } finally {
    globalThis.fetch = originalFetch;
    delete process.env.KEENA_DATA_FILE;
    await rm(dir, { recursive: true, force: true });
  }
});
