import { vi } from 'vitest'

/** One canned envelope per call, by URL; the call log is kept for the assertions. */
export function mockFetch(answer: (url: string) => unknown) {
  const calls: string[] = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString()
    calls.push(url)
    return new Response(JSON.stringify(answer(url)), { status: 200, headers: { 'Content-Type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fetchMock)
  return { calls, fetchMock }
}

export function envelope(data: unknown, meta: Record<string, unknown> = {}) {
  return { data, error: null, meta }
}
