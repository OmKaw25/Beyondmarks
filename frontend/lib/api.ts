export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: unknown = {}) { super(message); }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...options, credentials: 'same-origin', cache: 'no-store', headers: { 'Content-Type': 'application/json', ...options.headers } });
  } catch { throw new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the backend. Check your connection and try again.'); }
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, body?.error?.code ?? 'REQUEST_FAILED', body?.error?.message ?? 'The request could not be completed.', body?.error?.details);
  return body.data as T;
}

export function post<T>(path: string, value?: unknown) {
  return api<T>(path, { method: 'POST', body: value === undefined ? undefined : JSON.stringify(value) });
}

export function message(error: unknown): string { return error instanceof Error ? error.message : 'Something went wrong. Please try again.'; }
