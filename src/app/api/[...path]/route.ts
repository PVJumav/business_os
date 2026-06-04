export const runtime = "edge";

const BACKEND_URL = (process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

function backendUrl(path: string[], request: Request) {
  const incomingUrl = new URL(request.url);
  const target = new URL(`${BACKEND_URL}/api/${path.join("/")}`);
  target.search = incomingUrl.search;
  return target;
}

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  if (!BACKEND_URL) {
    return Response.json(
      { detail: "Backend API URL is not configured. Set BACKEND_API_URL or NEXT_PUBLIC_API_URL in Cloudflare Pages." },
      { status: 502 },
    );
  }

  const { path } = await context.params;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("x-forwarded-host");

  const response = await fetch(backendUrl(path, request), {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    redirect: "manual",
  });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
