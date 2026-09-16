import { TAXONOMY_RULES } from "./keena-icp";
import { queryNpiOrganizations, type NpiResult } from "./npi";
import { isoWeekKey, scoreNpiRecord, type Lead } from "./scoring";
import { leadsAddedThisWeek, loadPipeline, savePipeline, type RefreshRun } from "./store";

export const WEEKLY_LEAD_TARGET = 15;

/**
 * Distinct taxonomy queries to send this run. There are more taxonomy rules
 * than we want to query every run, so rotate a subset by ISO week number to
 * spread real API traffic and get variety across weeks while staying well
 * under the registry's rate limits.
 */
function taxonomiesForWeek(isoWeek: string, count: number): string[] {
  const all = Array.from(new Set(TAXONOMY_RULES.map((r) => r.match)));
  const weekNum = Number(isoWeek.split("-W")[1] ?? "0");
  const start = (weekNum * 3) % all.length;
  const picked: string[] = [];
  for (let i = 0; i < Math.min(count, all.length); i++) {
    picked.push(all[(start + i) % all.length]);
  }
  return picked;
}

export interface RefreshResult {
  run: RefreshRun;
  addedLeads: Lead[];
  totalLeadsThisWeek: number;
}

/**
 * Pull real organizations from the CMS NPI Registry, score them against
 * Keena's ICP, and top up this week's pipeline up to WEEKLY_LEAD_TARGET new
 * leads. Already-seen NPI numbers (from any prior week) are never re-added.
 * Per-taxonomy fetch failures are recorded but don't abort the whole run.
 */
export async function refreshWeeklyLeads(now: Date = new Date()): Promise<RefreshResult> {
  const isoWeek = isoWeekKey(now);
  const data = await loadPipeline();
  const seenNpiNumbers = new Set(data.leads.map((l) => l.npiNumber));
  const alreadyThisWeek = leadsAddedThisWeek(data, isoWeek);
  const remaining = Math.max(0, WEEKLY_LEAD_TARGET - alreadyThisWeek);

  const errors: string[] = [];
  const candidates: Lead[] = [];
  let queried = 0;

  if (remaining > 0) {
    const taxonomies = taxonomiesForWeek(isoWeek, 6);
    for (const taxonomyDescription of taxonomies) {
      let results: NpiResult[] = [];
      try {
        results = await queryNpiOrganizations({ taxonomyDescription, limit: 20 });
        queried += results.length;
      } catch (err) {
        errors.push(`${taxonomyDescription}: ${(err as Error).message}`);
        continue;
      }
      for (const record of results) {
        if (seenNpiNumbers.has(record.number)) continue;
        const lead = scoreNpiRecord(record, isoWeek, now);
        if (!lead) continue;
        seenNpiNumbers.add(record.number);
        candidates.push(lead);
      }
    }
  }

  candidates.sort((a, b) => b.fit - a.fit);
  const toAdd = candidates.slice(0, remaining);

  data.leads.push(...toAdd);
  const run: RefreshRun = {
    runAt: now.toISOString(),
    isoWeek,
    added: toAdd.length,
    queried,
    errors,
  };
  data.runs.push(run);
  await savePipeline(data);

  return {
    run,
    addedLeads: toAdd,
    totalLeadsThisWeek: alreadyThisWeek + toAdd.length,
  };
}
