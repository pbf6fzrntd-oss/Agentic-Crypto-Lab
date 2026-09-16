import { NextResponse } from "next/server";
import { updateLead } from "@/lib/store";
import { PIPELINE_STAGES, type PipelineStage } from "@/lib/scoring";

export const runtime = "nodejs";

const VALID_STAGES = new Set(PIPELINE_STAGES.map((s) => s.value));

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = (await request.json()) as { stage?: string; notes?: string };

  const patch: { stage?: PipelineStage; notes?: string } = {};
  if (typeof body.stage === "string") {
    if (!VALID_STAGES.has(body.stage as PipelineStage)) {
      return NextResponse.json({ error: `Invalid stage: ${body.stage}` }, { status: 400 });
    }
    patch.stage = body.stage as PipelineStage;
  }
  if (typeof body.notes === "string") {
    patch.notes = body.notes;
  }

  const lead = await updateLead(id, patch);
  if (!lead) {
    return NextResponse.json({ error: "Lead not found" }, { status: 404 });
  }
  return NextResponse.json({ lead });
}
