/**
 * Ingest a JSON file of RawCandidate[] (found via WebSearch — see
 * WEEKLY_SEARCH_RUNBOOK.md) into the pipeline: score, dedupe, cap at 15/week,
 * persist to data/pipeline.json.
 *
 * Usage: npm run leads:ingest -- path/to/candidates.json
 */
import { readFile } from "node:fs/promises";
import { ingestCandidates } from "../lib/ingest";
import type { RawCandidate } from "../lib/scoring";

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error("Usage: npm run leads:ingest -- path/to/candidates.json");
    process.exitCode = 1;
    return;
  }

  const raw = await readFile(file, "utf8");
  const candidates = JSON.parse(raw) as RawCandidate[];
  if (!Array.isArray(candidates)) {
    throw new Error(`${file} must contain a JSON array of candidates`);
  }

  const result = await ingestCandidates(candidates);
  const r = result.run;
  console.log(
    `[keena-growth-ops] week ${r.isoWeek}: reviewed ${r.candidatesReviewed}, added ${r.added}, ` +
      `${result.totalLeadsThisWeek} total this week`
  );
  console.log(
    `[keena-growth-ops] skipped: ${r.skippedDuplicate} duplicate, ${r.skippedOutOfIcp} out-of-ICP, ` +
      `${r.skippedExpired} expired, ${r.skippedOverTarget} over this week's target`
  );
  for (const lead of result.addedLeads) {
    console.log(`  + [${lead.fit}] ${lead.organization} — ${lead.title} (${lead.serviceLine})`);
  }
}

main().catch((err) => {
  console.error("[keena-growth-ops] ingest failed:", err);
  process.exitCode = 1;
});
