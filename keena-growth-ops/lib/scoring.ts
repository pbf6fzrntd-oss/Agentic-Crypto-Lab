import { bestServiceLineMatch, regionForState } from "./keena-icp";
import { isRecentDate, parseNpiDate, type NpiResult } from "./npi";

export type Discovery = "signal" | "prospect";

export interface Lead {
  id: string;
  npiNumber: string;
  company: string;
  initials: string;
  city: string;
  state: string;
  location: string;
  discovery: Discovery;
  fit: number;
  signal: string;
  focus: string;
  matchedTaxonomy: string;
  weekAdded: string;
  addedAt: string;
  stage: PipelineStage;
  notes: string;
}

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

function initialsFor(name: string): string {
  const words = name.replace(/[^A-Za-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
  if (words.length === 0) return "??";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

/**
 * Turn one real NPI Registry organization record into a scored pipeline
 * lead, or return null if it doesn't match any Keena service line at all
 * (i.e. it's out of ICP and shouldn't be surfaced).
 */
export function scoreNpiRecord(record: NpiResult, isoWeek: string, now: Date): Lead | null {
  const company = record.basic.organization_name?.trim();
  if (!company) return null;

  const taxonomyDescs = record.taxonomies.map((t) => t.desc);
  const match = bestServiceLineMatch(taxonomyDescs);
  if (!match) return null;

  const address = record.addresses.find((a) => a.state) ?? record.addresses[0];
  const state = address?.state ?? "";
  const city = address?.city ?? "";

  const recentlyUpdated = isRecentDate(record.basic.last_updated, 30, now);
  const recentlyEnumerated = isRecentDate(record.basic.enumeration_date, 90, now);

  let fit = match.baseFit;
  let signal: string;
  let discovery: Discovery;

  if (recentlyEnumerated) {
    fit = Math.min(99, fit + 8);
    discovery = "signal";
    signal = "Newly registered NPI organization";
  } else if (recentlyUpdated) {
    fit = Math.min(99, fit + 4);
    discovery = "signal";
    signal = "NPI record updated in the last 30 days";
  } else {
    discovery = "prospect";
    signal = "Matches Keena's ideal customer profile";
  }

  return {
    id: record.number,
    npiNumber: record.number,
    company,
    initials: initialsFor(company),
    city,
    state,
    location: regionForState(state),
    discovery,
    fit,
    signal,
    focus: match.serviceLine,
    matchedTaxonomy: match.matchedOn,
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

export { parseNpiDate };
