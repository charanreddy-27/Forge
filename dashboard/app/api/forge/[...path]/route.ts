// Thin proxy so browser code reaches the agent layer without CORS or
// build-time API URLs: /api/forge/<path> → ${FORGE_API_URL}/<path>.
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.FORGE_API_URL ?? "http://localhost:8000";

async function forward(request: NextRequest, path: string[]): Promise<NextResponse> {
  const target = `${API_URL}/${path.join("/")}${request.nextUrl.search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();

  const response = await fetch(target, {
    method: request.method,
    headers: { "Content-Type": "application/json" },
    body,
    cache: "no-store",
  });

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

type Context = { params: { path: string[] } };

export const GET = (request: NextRequest, { params }: Context) => forward(request, params.path);
export const POST = (request: NextRequest, { params }: Context) => forward(request, params.path);
export const PUT = (request: NextRequest, { params }: Context) => forward(request, params.path);
export const DELETE = (request: NextRequest, { params }: Context) => forward(request, params.path);
