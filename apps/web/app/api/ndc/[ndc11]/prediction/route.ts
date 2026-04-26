import { NextResponse } from "next/server";

import { fetchApi } from "../../../../../lib/api";

export async function GET(
  request: Request,
  { params }: { params: { ndc11: string } },
) {
  const { searchParams } = new URL(request.url);
  const months = searchParams.get("months") ?? "12";
  const model = searchParams.get("model") ?? "lightgbm";
  const result = await fetchApi(`/ndc/${encodeURIComponent(params.ndc11)}/pricing/prediction`, { months, model });

  return NextResponse.json(result, { status: result.ok ? 200 : result.status || 500 });
}
