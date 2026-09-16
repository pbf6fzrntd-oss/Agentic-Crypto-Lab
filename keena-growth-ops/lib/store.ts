import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Lead, PipelineStage } from "./scoring";

export interface RefreshRun {
  runAt: string;
  isoWeek: string;
  added: number;
  queried: number;
  errors: string[];
}

export interface PipelineData {
  leads: Lead[];
  runs: RefreshRun[];
}

// Read lazily (not cached at module load) so tests can point different
// runs at different temp files via KEENA_DATA_FILE within the same process.
function dataFile(): string {
  return process.env.KEENA_DATA_FILE ?? path.join(process.cwd(), "data", "pipeline.json");
}

const EMPTY: PipelineData = { leads: [], runs: [] };

export async function loadPipeline(): Promise<PipelineData> {
  try {
    const raw = await readFile(dataFile(), "utf8");
    const parsed = JSON.parse(raw) as PipelineData;
    return { leads: parsed.leads ?? [], runs: parsed.runs ?? [] };
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return { ...EMPTY };
    throw err;
  }
}

export async function savePipeline(data: PipelineData): Promise<void> {
  const file = dataFile();
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(data, null, 2) + "\n", "utf8");
}

export function leadsAddedThisWeek(data: PipelineData, isoWeek: string): number {
  return data.leads.filter((l) => l.weekAdded === isoWeek).length;
}

export async function updateLead(
  id: string,
  patch: Partial<Pick<Lead, "stage" | "notes">>
): Promise<Lead | null> {
  const data = await loadPipeline();
  const lead = data.leads.find((l) => l.id === id);
  if (!lead) return null;
  if (patch.stage !== undefined) lead.stage = patch.stage as PipelineStage;
  if (patch.notes !== undefined) lead.notes = patch.notes;
  await savePipeline(data);
  return lead;
}
