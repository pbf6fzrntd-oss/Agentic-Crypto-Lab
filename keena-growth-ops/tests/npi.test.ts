import { test } from "node:test";
import assert from "node:assert/strict";
import { queryNpiOrganizations, isRecentDate, parseNpiDate } from "../lib/npi.ts";

test("queryNpiOrganizations parses a mocked NPI Registry v2.1 response", async () => {
  const originalFetch = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    calls.push(String(input));
    return new Response(
      JSON.stringify({
        result_count: 1,
        results: [
          {
            number: "1999999999",
            enumeration_type: "NPI-2",
            basic: { organization_name: "Mocked Health System", enumeration_date: "05/01/2020", last_updated: "05/01/2020" },
            addresses: [{ city: "Austin", state: "TX" }],
            taxonomies: [{ desc: "Health Care System", primary: true }],
          },
        ],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  try {
    const results = await queryNpiOrganizations({ taxonomyDescription: "Health Care System" });
    assert.equal(results.length, 1);
    assert.equal(results[0].basic.organization_name, "Mocked Health System");
    assert.match(calls[0], /npiregistry\.cms\.hhs\.gov/);
    assert.match(calls[0], /enumeration_type=NPI-2/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("queryNpiOrganizations throws on a non-2xx response", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async () => new Response("rate limited", { status: 429 })) as typeof fetch;
  try {
    await assert.rejects(() => queryNpiOrganizations({ taxonomyDescription: "x" }), /429/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("parseNpiDate / isRecentDate handle NPI's MM/DD/YYYY format", () => {
  const d = parseNpiDate("03/04/2026");
  assert.ok(d);
  assert.equal(d!.getFullYear(), 2026);
  assert.equal(d!.getMonth(), 2);
  assert.equal(d!.getDate(), 4);

  assert.equal(parseNpiDate("not-a-date"), null);
  assert.equal(isRecentDate("03/04/2026", 30, new Date("2026-03-10")), true);
  assert.equal(isRecentDate("01/01/2000", 30, new Date("2026-03-10")), false);
  assert.equal(isRecentDate(undefined, 30), false);
});
