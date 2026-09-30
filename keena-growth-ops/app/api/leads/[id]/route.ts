import { accessAllowed, mutationAllowed } from "@/lib/auth";
import { NextResponse } from "next/server";
import { updateLead } from "@/lib/store";
import { PIPELINE_STAGES, type PipelineStage } from "@/lib/scoring";

export const runtime = "nodejs";

const VALID_STAGES = new Set(PIPELINE_STAGES.map((s) => s.value));

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  if (!(await accessAllowed(request))) return NextResponse.json({error:"Unauthorized"},{status:401});
  if (!mutationAllowed(request)) return NextResponse.json({error:"Unapproved origin"},{status:403});
  try {
    const {id}=await params;
    const raw=await request.text(); if(raw.length>12000) return NextResponse.json({error:"Request too large"},{status:413});
    const body=JSON.parse(raw);
    if(!body || Array.isArray(body) || !Number.isInteger(body.version) || body.version<0 || !Object.keys(body).every(k=>["stage","notes","owner","version"].includes(k)) || (body.stage!==undefined && !VALID_STAGES.has(body.stage)) || (body.notes!==undefined && (typeof body.notes!=="string" || body.notes.length>5000)) || (body.owner!==undefined && (typeof body.owner!=="string" || body.owner.length>120)))return NextResponse.json({error:"Invalid update"},{status:400});
    const patch: {stage?:PipelineStage;notes?:string;owner?:string}={};
    for(const field of ["stage","notes","owner"] as const)if(body[field]!==undefined)patch[field]=body[field];
    const lead=await updateLead(id,patch,undefined,body.version);
    if(!lead)return NextResponse.json({error:"Lead not found"},{status:404});
    return NextResponse.json({lead});
  } catch(error) { return NextResponse.json({error:error instanceof Error && error.message==="stale_version"?"Lead changed; reload before saving.":"Update could not be processed"},{status:error instanceof Error && error.message==="stale_version"?409:400}); }
}
