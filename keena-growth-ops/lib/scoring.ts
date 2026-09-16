import { bestServiceLineMatch } from "./keena-icp";

export type SourceType = "rfp" | "job_posting";

export type PipelineStage =
  | "new"
  | "contacted"
  | "qualified"
  | "meeting"
  | "proposal"
  | "won"
  | "lost";

export const PIPELINE_STAGES: { value: PipelineStage; label: string }[] = [
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "qualified", label: "Qualified" },
  { value: "meeting", label: "Meeting booked" },
  { value: "proposal", label: "Proposal sent" },
  { value: "won", label: "Won" },
  { value: "lost", label: "Lost" },
];

/**
 * A single RFP or job posting found via web search, before scoring. This is
 * the hand-off point between agentic discovery (a Claude session running
 * WebSearch per WEEKLY_SEARCH_RUNBOOK.md) and deterministic, tested scoring
 * code below — everything past this point is plain, unit-tested TypeScript.
 */
export interface RawCandidate {
  sourceType: SourceType;
  organization: string;
  title: string;
  /** Real, direct link to the posting/notice — required so a human can verify it. */
  url: string;
  /** Free text (title + summary) the keyword rules are matched against. */
  text: string;
  location?: string;
  /** ISO date the RFP/job was posted or issued, if known. */
  postedDate?: string;
  /** ISO date an RFP's response window closes, if known. Irrelevant for job postings. */
  deadline?: string;
}

export interface Lead {
  id: string;
  sourceType: SourceType;
  organization: string;
  initials: string;
  title: string;
  url: string;
  location: string;
  postedDate: string | null;
  deadline: string | null;
  fit: number;
  serviceLine: string;
  matchedKeyword: string;
  signal: string;
  weekAdded: string;
  addedAt: string;
  stage: PipelineStage;
  notes: string;
}

function initialsFor(name: string): string {
  const words = name.replace(/[^A-Za-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
  if (words.length === 0) return "??";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function daysBetween(a: Date, b: Date): number {
  return (a.getTime() - b.getTime()) / (24 * 60 * 60 * 1000);
}

/**
 * Score one raw candidate, or return null if it should never become a lead:
 * out of ICP (no keyword match), or an RFP whose response deadline has
 * already passed. A stale "open" RFP is worse than no lead at all.
 */
export function scoreCandidate(candidate: RawCandidate, isoWeek: string, now: Date): Lead | null {
  if (!candidate.organization?.trim() || !candidate.url?.trim()) return null;

  const match = bestServiceLineMatch(candidate.text);
  if (!match) return null;

  if (candidate.sourceType === "rfp" && candidate.deadline) {
    const deadline = new Date(candidate.deadline);
    if (!Number.isNaN(deadline.getTime()) && deadline.getTime() < now.getTime()) {
      return null; // expired — never surface a closed RFP as an open lead
    }
  }

  let fit = match.baseFit;
  let signal: string;

  if (candidate.sourceType === "rfp") {
    fit += 5; // an active procurement is a more direct buying signal than a job req
    signal = candidate.deadline
      ? `Open RFP, responses due ${candidate.deadline}`
      : "Open RFP";
  } else {
    signal = "Open job requisition";
  }

  if (candidate.postedDate) {
    const posted = new Date(candidate.postedDate);
    if (!Number.isNaN(posted.getTime())) {
      const age = daysBetween(now, posted);
      if (age >= 0 && age <= 14) fit += 6;
      else if (age >= 0 && age <= 30) fit += 3;
    }
  }
  fit = Math.min(99, fit);

  return {
    id: candidate.url,
    sourceType: candidate.sourceType,
    organization: candidate.organization.trim(),
    initials: initialsFor(candidate.organization),
    title: candidate.title.trim(),
    url: candidate.url.trim(),
    location: candidate.location?.trim() || "Unspecified",
    postedDate: candidate.postedDate ?? null,
    deadline: candidate.deadline ?? null,
    fit,
    serviceLine: match.serviceLine,
    matchedKeyword: match.matchedOn,
    signal,
    weekAdded: isoWeek,
    addedAt: now.toISOString(),
    stage: "new",
    notes: "",
  };
}

/** ISO week identifier, e.g. "2026-W38", used to enforce the weekly cadence. */
export function isoWeekKey(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}
