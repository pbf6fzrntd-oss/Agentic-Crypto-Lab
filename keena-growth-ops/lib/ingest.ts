import { isoWeekKey, scoreCandidate, type Lead, type RawCandidate } from "./scoring";
import { leadsAddedThisWeek, mutatePipeline, type IngestRun } from "./store";

export const WEEKLY_LEAD_TARGET = 15;

export interface IngestResult {
  run: IngestRun;
  addedLeads: Lead[];
  totalLeadsThisWeek: number;
}

/**
 * Deterministic, pure-data half of the pipeline: takes candidates a Claude
 * session already found via WebSearch (see WEEKLY_SEARCH_RUNBOOK.md) and
 * scores, dedupes, caps, and persists them. No network calls happen here —
 * that's the point: discovery is agentic and un-mockable, but everything
 * after "here is a list of real URLs" is plain, testable code.
 */
export async function ingestCandidates(
  candidates: RawCandidate[],
  now: Date = new Date(),
  file?: string
): Promise<IngestResult> {
  const isoWeek = isoWeekKey(now);
  return mutatePipeline((data) => {
  const seenUrls = new Set(data.leads.map((l) => canonicalUrl(l.url)));
  const alreadyThisWeek = leadsAddedThisWeek(data, isoWeek);
  const remaining = Math.max(0, WEEKLY_LEAD_TARGET - alreadyThisWeek);

  let skippedDuplicate = 0;
  let skippedOutOfIcp = 0;
  let skippedExpired = 0;
  const scored: Lead[] = [];

  for (let candidate of candidates) {
    candidate = { ...candidate, url: canonicalUrl(candidate.url) };
    if (seenUrls.has(candidate.url)) {
      const existing = data.leads.find(l => canonicalUrl(l.url) === candidate.url);
      if (existing && candidate.checkedAt && !Number.isNaN(Date.parse(candidate.checkedAt))) { existing.checkedAt = candidate.checkedAt; existing.version = (existing.version ?? 0) + 1; }
      skippedDuplicate++;
      continue;
    }
    const lead = scoreCandidate(candidate, isoWeek, now);
    if (!lead) {
      const isExpired =
        candidate.sourceType === "rfp" &&
        !!candidate.deadline &&
        !Number.isNaN(new Date(candidate.deadline).getTime()) &&
        new Date(candidate.deadline).getTime() < now.getTime();
      if (isExpired) skippedExpired++;
      else skippedOutOfIcp++;
      continue;
    }
    seenUrls.add(candidate.url);
    scored.push(lead);
  }

  scored.sort((a, b) => b.fit - a.fit);
  const toAdd = scored.slice(0, remaining);
  const skippedOverTarget = scored.length - toAdd.length;

  data.leads.push(...toAdd);
  const run: IngestRun = {
    runAt: now.toISOString(),
    isoWeek,
    candidatesReviewed: candidates.length,
    added: toAdd.length,
    skippedDuplicate,
    skippedOutOfIcp,
    skippedExpired,
    skippedOverTarget,
  };
  data.runs.push(run);


  return {
    run,
    addedLeads: toAdd,
    totalLeadsThisWeek: alreadyThisWeek + toAdd.length,
  };
  }, file);
}

export function canonicalUrl(value: string): string { const url = new URL(value); if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) throw Error("Invalid source URL"); url.hash=""; for(const name of [...url.searchParams.keys()]) if(name.startsWith("utm_") || ["fbclid","gclid"].includes(name)) url.searchParams.delete(name); url.searchParams.sort(); return url.toString().replace(/\/$/, ""); }
