import { NextResponse } from "next/server";
import { isoWeekKey } from "@/lib/scoring";
import { leadsAddedThisWeek, loadPipeline } from "@/lib/store";
import { WEEKLY_LEAD_TARGET } from "@/lib/leadgen";

export const runtime = "nodejs";

export async function GET() {
  const data = await loadPipeline();
  const isoWeek = isoWeekKey(new Date());
  const lastRun = data.runs.at(-1) ?? null;
  return NextResponse.json({
    leads: data.leads,
    isoWeek,
    addedThisWeek: leadsAddedThisWeek(data, isoWeek),
    weeklyTarget: WEEKLY_LEAD_TARGET,
    lastRun,
  });
}
