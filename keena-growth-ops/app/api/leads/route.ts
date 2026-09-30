import { accessAllowed } from "@/lib/auth";
import { NextResponse } from "next/server";
import { isoWeekKey } from "@/lib/scoring";
import { leadsAddedThisWeek, loadPipeline } from "@/lib/store";
import { WEEKLY_LEAD_TARGET } from "@/lib/ingest";

export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!(await accessAllowed(request))) return NextResponse.json({error:"Unauthorized"},{status:401});
  const data = await loadPipeline();
  const isoWeek = isoWeekKey(new Date());
  const lastRun = data.runs.at(-1) ?? null;
  return NextResponse.json({
    leads: data.leads,
    mode: process.env.KEENA_DEMO === "1" ? "example" : "pilot",
    isoWeek,
    addedThisWeek: leadsAddedThisWeek(data, isoWeek),
    weeklyTarget: WEEKLY_LEAD_TARGET,
    lastRun,
  });
}
