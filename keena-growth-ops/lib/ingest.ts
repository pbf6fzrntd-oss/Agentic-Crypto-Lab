import { isoWeekKey, scoreCandidate, type Lead, type RawCandidate } from "./scoring";
import { leadsAddedThisWeek, loadPipeline, savePipeline, type IngestRun } from "./store";

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
  const data = await loadPipeline(file);
  const seenUrls = new Set(data.leads.map((l) => l.url));
  const alreadyThisWeek = leadsAddedThisWeek(data, isoWeek);
  const remaining = Math.max(0, WEEKLY_LEAD_TARGET - alreadyThisWeek);

  let skippedDuplicate = 0;
  let skippedOutOfIcp = 0;
  let skippedExpired = 0;
  const scored: Lead[] = [];

  for (const candidate of candidates) {
    if (seenUrls.has(candidate.url)) {
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
  await savePipeline(data, file);

  return {
    run,
    addedLeads: toAdd,
    totalLeadsThisWeek: alreadyThisWeek + toAdd.length,
  };
}
