/**
 * Client for the CMS NPI Registry public API (https://npiregistry.cms.hhs.gov).
 *
 * This is a real, free, keyless, official U.S. government API. It is the
 * pipeline's real data feed: every lead in this app is a real healthcare
 * provider organization pulled from this registry, not synthetic data.
 *
 * Known limitation: outbound network access to npiregistry.cms.hhs.gov was
 * blocked by this sandbox's organization egress policy while this file was
 * written (403 at the proxy, confirmed via `curl`). The request/response
 * shapes below follow the NPI Registry API v2.1 documentation and are
 * covered by mocked-fetch unit tests in tests/npi.test.ts, but this client
 * has not yet been exercised against a live response. Run
 * `npm run leads:refresh` once from an environment with real network access
 * before trusting it on a schedule — see README.md.
 */

const NPI_API_BASE = "https://npiregistry.cms.hhs.gov/api/";

export interface NpiAddress {
  address_1?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  telephone_number?: string;
}

export interface NpiTaxonomy {
  desc: string;
  primary: boolean;
  state?: string;
}

export interface NpiResult {
  number: string;
  enumeration_type: "NPI-1" | "NPI-2";
  basic: {
    organization_name?: string;
    name?: string;
    enumeration_date?: string;
    last_updated?: string;
    status?: string;
  };
  addresses: NpiAddress[];
  taxonomies: NpiTaxonomy[];
}

interface NpiApiResponse {
  result_count: number;
  results: NpiResult[];
}

export interface NpiQuery {
  taxonomyDescription: string;
  state?: string;
  limit?: number;
  skip?: number;
}

/**
 * Query the NPI Registry for organizational providers (NPI-2, i.e. real
 * businesses/facilities, not individual clinicians) matching a taxonomy
 * description. Throws on network failure or a non-2xx response; callers
 * decide how to handle a partial-batch failure.
 */
export async function queryNpiOrganizations(query: NpiQuery): Promise<NpiResult[]> {
  const params = new URLSearchParams({
    version: "2.1",
    enumeration_type: "NPI-2",
    taxonomy_description: query.taxonomyDescription,
    limit: String(query.limit ?? 20),
    skip: String(query.skip ?? 0),
  });
  if (query.state) params.set("state", query.state);

  const url = `${NPI_API_BASE}?${params.toString()}`;
  const res = await fetch(url, {
    headers: {
      Accept: "application/json",
      // Public, keyless government API with no auth — a descriptive UA is
      // just good etiquette, not a requirement.
      "User-Agent": "keena-growth-ops/1.0 (+https://github.com/pbf6fzrntd-oss/agentic-crypto-lab)",
    },
  });
  if (!res.ok) {
    throw new Error(`NPI Registry API returned ${res.status} ${res.statusText} for ${url}`);
  }
  const body = (await res.json()) as NpiApiResponse;
  return body.results ?? [];
}

/** True if the given NPI-formatted date string falls within the last `withinDays` days. */
export function isRecentDate(dateStr: string | undefined, withinDays: number, now: Date = new Date()): boolean {
  if (!dateStr) return false;
  const parsed = parseNpiDate(dateStr);
  if (!parsed) return false;
  const ageMs = now.getTime() - parsed.getTime();
  return ageMs >= 0 && ageMs <= withinDays * 24 * 60 * 60 * 1000;
}

/** NPI dates are formatted MM/DD/YYYY. */
export function parseNpiDate(dateStr: string): Date | null {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(dateStr.trim());
  if (!m) return null;
  const [, mm, dd, yyyy] = m;
  return new Date(Number(yyyy), Number(mm) - 1, Number(dd));
}
