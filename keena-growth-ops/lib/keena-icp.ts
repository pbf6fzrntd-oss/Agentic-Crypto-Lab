/**
 * Keena's ideal-customer-profile map: which real-world provider-organization
 * taxonomies map to which Keena service line, and how strong that fit is.
 *
 * Source of truth for taxonomy strings: the NUCC Health Care Provider
 * Taxonomy code set, as returned verbatim by the CMS NPI Registry API in
 * each result's `taxonomies[].desc` field.
 */
export type ServiceLine =
  | "EHR Conversions"
  | "Interoperability"
  | "Epic Consulting"
  | "Financial Consulting"
  | "KeenaArchive"
  | "Workflow Efficiency"
  | "Document Management"
  | "Clinical Consulting"
  | "Managed Interfaces"
  | "Custom Development";

export interface TaxonomyRule {
  /** Substring match (case-insensitive) against the NPI taxonomy description. */
  match: string;
  serviceLine: ServiceLine;
  /** Base fit score 0-100 for an org whose primary taxonomy matches. */
  baseFit: number;
}

export const TAXONOMY_RULES: TaxonomyRule[] = [
  { match: "General Acute Care Hospital", serviceLine: "EHR Conversions", baseFit: 90 },
  { match: "Critical Access Hospital", serviceLine: "EHR Conversions", baseFit: 88 },
  { match: "Psychiatric Hospital", serviceLine: "EHR Conversions", baseFit: 78 },
  { match: "Rehabilitation Hospital", serviceLine: "EHR Conversions", baseFit: 78 },
  { match: "Health Care System", serviceLine: "Epic Consulting", baseFit: 92 },
  { match: "Multi-Specialty", serviceLine: "Interoperability", baseFit: 84 },
  { match: "Clinic/Center", serviceLine: "Workflow Efficiency", baseFit: 76 },
  { match: "Ambulatory Health Care Facility", serviceLine: "Workflow Efficiency", baseFit: 74 },
  { match: "Ambulatory Surgical Center", serviceLine: "Workflow Efficiency", baseFit: 75 },
  { match: "Home Health", serviceLine: "Document Management", baseFit: 70 },
  { match: "Hospice Care", serviceLine: "Document Management", baseFit: 68 },
  { match: "Skilled Nursing Facility", serviceLine: "KeenaArchive", baseFit: 72 },
  { match: "Nursing Facility", serviceLine: "KeenaArchive", baseFit: 70 },
  { match: "Managed Care", serviceLine: "Financial Consulting", baseFit: 82 },
  { match: "Health Maintenance Organization", serviceLine: "Financial Consulting", baseFit: 80 },
  { match: "Preferred Provider Organization", serviceLine: "Financial Consulting", baseFit: 78 },
  { match: "Community Health Center", serviceLine: "Clinical Consulting", baseFit: 74 },
  { match: "Rural Health Clinic", serviceLine: "Clinical Consulting", baseFit: 72 },
  { match: "Diagnostic Radiology", serviceLine: "Managed Interfaces", baseFit: 71 },
  { match: "Clinical Medical Laboratory", serviceLine: "Managed Interfaces", baseFit: 71 },
  { match: "Pharmacy", serviceLine: "Custom Development", baseFit: 65 },
];

export function bestServiceLineMatch(taxonomyDescriptions: string[]): {
  serviceLine: ServiceLine;
  baseFit: number;
  matchedOn: string;
} | null {
  let best: { serviceLine: ServiceLine; baseFit: number; matchedOn: string } | null = null;
  for (const desc of taxonomyDescriptions) {
    for (const rule of TAXONOMY_RULES) {
      if (desc.toLowerCase().includes(rule.match.toLowerCase())) {
        if (!best || rule.baseFit > best.baseFit) {
          best = { serviceLine: rule.serviceLine, baseFit: rule.baseFit, matchedOn: desc };
        }
      }
    }
  }
  return best;
}

/** Region grouping used for the "location" facet shown in the UI. */
export function regionForState(state: string | undefined): string {
  const s = (state ?? "").toUpperCase();
  const northeast = ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"];
  const midwest = ["OH", "MI", "IN", "WI", "IL", "MN", "IA", "MO", "ND", "SD", "NE", "KS"];
  const south = ["DE", "MD", "DC", "VA", "WV", "NC", "SC", "GA", "FL", "KY", "TN", "AL", "MS", "AR", "LA", "OK", "TX"];
  const west = ["MT", "ID", "WY", "CO", "NM", "AZ", "UT", "NV", "WA", "OR", "CA", "AK", "HI"];
  if (northeast.includes(s)) return "Northeast";
  if (midwest.includes(s)) return "Midwest";
  if (south.includes(s)) return "Southeast";
  if (west.includes(s)) return "West";
  return "National";
}
