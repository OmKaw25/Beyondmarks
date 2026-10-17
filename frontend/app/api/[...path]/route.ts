import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.every(segment => /^[a-zA-Z0-9_-]+$/.test(segment))) return NextResponse.json({ error: { code: 'INVALID_PATH', message: 'Invalid request path.' } }, { status: 400 });
  const origin = request.headers.get('origin');
  if (request.method === 'POST' && origin) {
    let trusted = false;
    try { const url = new URL(origin); trusted = ['http:', 'https:'].includes(url.protocol) && url.host === request.headers.get('host'); } catch {}
    if (!trusted) return NextResponse.json({ error: { code: 'ORIGIN_REJECTED', message: 'This request came from an untrusted origin.' } }, { status: 403 });
  }
  const body = request.method === 'POST' ? await request.text() : undefined;
  if (body && body.length > (path[0]==='classroom'?262144:65536)) return NextResponse.json({ error: { code: 'REQUEST_TOO_LARGE', message: 'This response is too long.' } }, { status: 413 });
  try {
    const upstream = await fetch(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/api/${path.join('/')}${request.nextUrl.search}`, {
      method: request.method, body, cache: 'no-store', signal: AbortSignal.timeout(path[0]==='classroom'?65000:15000),
      headers: { 'Content-Type': 'application/json', ...(request.headers.get('cookie') ? { Cookie: request.headers.get('cookie')! } : {}), ...(origin ? { Origin: origin } : {}) },
    });
    const response = new NextResponse(await upstream.text(), { status: upstream.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    for (const cookie of upstream.headers.getSetCookie()) response.headers.append('Set-Cookie', cookie);
    return response;
  } catch { return NextResponse.json({ error: { code: 'BACKEND_UNAVAILABLE', message: 'The learning backend is not reachable. Start the backend and check its connection, then try again.', details: {} } }, { status: 503 }); }
}
export const GET = proxy;
export const POST = proxy;
