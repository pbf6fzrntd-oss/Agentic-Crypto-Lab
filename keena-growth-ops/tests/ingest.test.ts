import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { ingestCandidates, WEEKLY_LEAD_TARGET } from "../lib/ingest.ts";
import { loadPipeline } from "../lib/store.ts";
import type { RawCandidate } from "../lib/scoring.ts";

function candidate(i: number, overrides: Partial<RawCandidate> = {}): RawCandidate {
  return {
    sourceType: "rfp",
    organization: `Org ${i}`,
    title: `RFP ${i}`,
    url: `https://example.gov/rfp/${i}`,
    text: `Requesting proposals for electronic health record conversion services (item ${i}).`,
    postedDate: "2026-09-01",
    deadline: "2026-12-31",
    ...overrides,
  };
}

// Each test gets its own temp file passed explicitly (rather than mutating
// a shared process.env), so tests stay isolated regardless of whether the
// test runner executes this file's tests sequentially or concurrently.
async function withTempFile<T>(fn: (file: string) => Promise<T>): Promise<T> {
  const dir = await mkdtemp(path.join(tmpdir(), "keena-test-"));
  const file = path.join(dir, "pipeline.json");
  try {
    return await fn(file);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

test("ingestCandidates caps additions at the weekly target", async () => {
  await withTempFile(async (file) => {
    const candidates = Array.from({ length: 20 }, (_, i) => candidate(i));
    const result = await ingestCandidates(candidates, new Date("2026-09-16"), file);
    assert.equal(result.run.added, WEEKLY_LEAD_TARGET);
    assert.equal(result.run.candidatesReviewed, 20);
    assert.equal(result.run.skippedOverTarget, 20 - WEEKLY_LEAD_TARGET);
    assert.equal(result.totalLeadsThisWeek, WEEKLY_LEAD_TARGET);
  });
});

test("ingestCandidates never re-adds a URL already in the pipeline, even in a later week", async () => {
  await withTempFile(async (file) => {
    const batch = Array.from({ length: 5 }, (_, i) => candidate(i));

    const first = await ingestCandidates(batch, new Date("2026-09-16"), file);
    assert.equal(first.run.added, 5);

    // Same candidates offered again a week later: all duplicates.
    const second = await ingestCandidates(batch, new Date("2026-09-23"), file);
    assert.equal(second.run.added, 0);
    assert.equal(second.run.skippedDuplicate, 5);

    const data = await loadPipeline(file);
    assert.equal(data.leads.length, 5);
  });
});

test("ingestCandidates drops out-of-ICP and expired-RFP candidates with accurate counters", async () => {
  await withTempFile(async (file) => {
    const candidates = [
      candidate(1),
      candidate(2, { text: "Requesting proposals for parking garage repaving." }), // out of ICP
      candidate(3, { deadline: "2020-01-01" }), // expired
    ];
    const result = await ingestCandidates(candidates, new Date("2026-09-16"), file);
    assert.equal(result.run.added, 1);
    assert.equal(result.run.skippedOutOfIcp, 1);
    assert.equal(result.run.skippedExpired, 1);
  });
});

test("ingestCandidates tops up a partially-filled week rather than re-capping from zero", async () => {
  await withTempFile(async (file) => {
    const now = new Date("2026-09-16");
    const firstBatch = Array.from({ length: 10 }, (_, i) => candidate(i));
    const first = await ingestCandidates(firstBatch, now, file);
    assert.equal(first.run.added, 10);

    const secondBatch = Array.from({ length: 10 }, (_, i) => candidate(i + 100));
    const second = await ingestCandidates(secondBatch, now, file);
    assert.equal(second.run.added, WEEKLY_LEAD_TARGET - 10);
    assert.equal(second.totalLeadsThisWeek, WEEKLY_LEAD_TARGET);
  });
});
