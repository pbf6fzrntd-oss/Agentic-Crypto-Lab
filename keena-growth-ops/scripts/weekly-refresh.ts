/**
 * Standalone weekly refresh entry point — run this on a schedule (see
 * .github/workflows/keena-weekly-leads.yml) to top the pipeline up to 15
 * new leads for the current ISO week, independent of the Next.js server.
 *
 * Usage: npm run leads:refresh
 */
import { refreshWeeklyLeads } from "../lib/leadgen";

async function main() {
  const result = await refreshWeeklyLeads();
  console.log(
    `[keena-growth-ops] week ${result.run.isoWeek}: added ${result.run.added} lead(s) ` +
      `(queried ${result.run.queried} records), ${result.totalLeadsThisWeek} total this week`
  );
  if (result.run.errors.length > 0) {
    console.warn(`[keena-growth-ops] ${result.run.errors.length} taxonomy quer${result.run.errors.length === 1 ? "y" : "ies"} failed:`);
    for (const e of result.run.errors) console.warn(`  - ${e}`);
  }
}

main().catch((err) => {
  console.error("[keena-growth-ops] weekly refresh failed:", err);
  process.exitCode = 1;
});
