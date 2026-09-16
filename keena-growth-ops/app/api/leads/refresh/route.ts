import { NextResponse } from "next/server";
import { refreshWeeklyLeads } from "@/lib/leadgen";

export const runtime = "nodejs";

export async function POST() {
  try {
    const result = await refreshWeeklyLeads();
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message },
      { status: 502 }
    );
  }
}
