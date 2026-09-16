import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Lead, PipelineStage } from "./scoring";

export interface IngestRun {
  runAt: string;
  isoWeek: string;
  candidatesReviewed: number;
  added: number;
  skippedDuplicate: number;
  skippedOutOfIcp: number;
  skippedExpired: number;
  skippedOverTarget: number;
}

export interface PipelineData {
  leads: Lead[];
  runs: IngestRun[];
}

function defaultDataFile(): string {
  return process.env.KEENA_DATA_FILE ?? path.join(process.cwd(), "data", "pipeline.json");
}

export async function loadPipeline(file: string = defaultDataFile()): Promise<PipelineData> {
  try {
    const raw = await readFile(file, "utf8");
    const parsed = JSON.parse(raw) as PipelineData;
    return { leads: parsed.leads ?? [], runs: parsed.runs ?? [] };
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return { leads: [], runs: [] };
    throw err;
  }
}

export async function savePipeline(data: PipelineData, file: string = defaultDataFile()): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(data, null, 2) + "\n", "utf8");
}

export function leadsAddedThisWeek(data: PipelineData, isoWeek: string): number {
  return data.leads.filter((l) => l.weekAdded === isoWeek).length;
}

export async function updateLead(
  id: string,
  patch: Partial<Pick<Lead, "stage" | "notes">>,
  file: string = defaultDataFile()
): Promise<Lead | null> {
  const data = await loadPipeline(file);
  const lead = data.leads.find((l) => l.id === id);
  if (!lead) return null;
  if (patch.stage !== undefined) lead.stage = patch.stage as PipelineStage;
  if (patch.notes !== undefined) lead.notes = patch.notes;
  await savePipeline(data, file);
  return lead;
}
