import { ApiError, UnreachableError } from './errors'
import type { Envelope } from './types'

/** Every request goes to this origin under /api/v1 (criterion 65); the cookie rides along. */
export const API_BASE = '/api/v1'

function retryAfter(response: Response): number | null {
  const raw = response.headers.get('Retry-After')
  if (raw === null) return null
  const seconds = Number(raw)
  return Number.isFinite(seconds) ? Math.max(0, Math.ceil(seconds)) : null
}

async function readEnvelope<T>(response: Response): Promise<Envelope<T> | null> {
  try {
    return (await response.json()) as Envelope<T>
  } catch {
    return null
  }
}

/** Fetch a route and unwrap the envelope; a non-2xx answer becomes an `ApiError`. */
export async function request<T>(path: string, init: RequestInit = {}): Promise<Envelope<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { credentials: 'same-origin', ...init })
  } catch {
    throw new UnreachableError()
  }

  const body = await readEnvelope<T>(response)
  if (response.ok && body) return body
  if (response.status >= 502 && body === null) throw new UnreachableError()

  const error = body?.error
  throw new ApiError(
    response.status,
    error?.code ?? 'unknown_error',
    error?.message ?? `Request failed with ${response.status}`,
    retryAfter(response),
    error?.details ?? {},
  )
}

export function postJson<T>(path: string, payload: unknown): Promise<Envelope<T>> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
