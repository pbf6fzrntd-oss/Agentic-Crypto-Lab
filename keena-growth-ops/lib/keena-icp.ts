/**
 * Keena Healthcare Technology's real service lines (keenahealth.com) and
 * the keyword patterns in an RFP/job-posting title or summary that signal
 * a real-world need for each one. This is the ICP map for scoring RFP and
 * job-listing candidates found via web search — see WEEKLY_SEARCH_RUNBOOK.md.
 */
export type ServiceLine =
  | "EHR Conversions"
  | "KeenaArchive"
  | "Document Management"
  | "Interoperability"
  | "Epic Consulting"
  | "Clinical Consulting"
  | "Advisory Consulting"
  | "Custom Development"
  | "Population Health"
  | "Disaster Recovery"
  | "Patient Engagement"
  | "Financial Consulting"
  | "Workflow Efficiency";

export interface KeywordRule {
  match: RegExp;
  serviceLine: ServiceLine;
  baseFit: number;
}

export const KEYWORD_RULES: KeywordRule[] = [
  { match: /\b(EHR|electronic health record)s?\s*(conversion|migration|transition)/i, serviceLine: "EHR Conversions", baseFit: 92 },
  { match: /\blegacy\s*(EHR|system|application)s?\s*(archiv|retention|decommission|sunset)/i, serviceLine: "KeenaArchive", baseFit: 90 },
  { match: /\bdata\s*archiv(e|al|ing)\b|\brecords?\s*retention\b/i, serviceLine: "KeenaArchive", baseFit: 82 },
  { match: /\bdocument\s*management\b|\brecords?\s*management\b|\bimaging\s*(services|solution)\b|\bintelligent document processing\b|\bIDP\b/i, serviceLine: "Document Management", baseFit: 80 },
  { match: /\binteroperability\b|\bHL7\b|\bFHIR\b|\binterface engine\b|\bhealth information exchange\b|\bHIE\b/i, serviceLine: "Interoperability", baseFit: 86 },
  { match: /\bEpic\b.*(analyst|consult|bridges|implementation|go-live)/i, serviceLine: "Epic Consulting", baseFit: 88 },
  { match: /\bclinical informatics\b|\bclinical (advisory )?consult(ant|ing)\b|\bCMIO\b/i, serviceLine: "Clinical Consulting", baseFit: 78 },
  { match: /\badvisory (services|consulting)\b|\bEHR optimization\b|\bpractice management\b.*(optim|consult)/i, serviceLine: "Advisory Consulting", baseFit: 74 },
  { match: /\bcustom (software|application) development\b.*(healthcare|health)|\bhealthcare IT vendor\b/i, serviceLine: "Custom Development", baseFit: 76 },
  { match: /\bpopulation health\b/i, serviceLine: "Population Health", baseFit: 72 },
  { match: /\bdisaster recovery\b|\bbusiness continuity\b/i, serviceLine: "Disaster Recovery", baseFit: 72 },
  { match: /\bpatient (engagement|portal)\b/i, serviceLine: "Patient Engagement", baseFit: 70 },
  { match: /\brevenue cycle\b|\bclaims (processing|automation)\b|\bmedical billing\b/i, serviceLine: "Financial Consulting", baseFit: 76 },
  { match: /\bworkflow (efficiency|optimization)\b|\bclinical workflow\b/i, serviceLine: "Workflow Efficiency", baseFit: 74 },
];

export function bestServiceLineMatch(text: string): { serviceLine: ServiceLine; baseFit: number; matchedOn: string } | null {
  let best: { serviceLine: ServiceLine; baseFit: number; matchedOn: string } | null = null;
  for (const rule of KEYWORD_RULES) {
    const m = rule.match.exec(text);
    if (m && (!best || rule.baseFit > best.baseFit)) {
      best = { serviceLine: rule.serviceLine, baseFit: rule.baseFit, matchedOn: m[0] };
    }
  }
  return best;
}
