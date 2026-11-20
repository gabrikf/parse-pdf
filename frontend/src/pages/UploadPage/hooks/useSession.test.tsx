import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useSession } from './useSession'

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

function json(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...headers } })
}

const refused = () => json(429, { data: null, error: { code: 'rate_limited', message: 'Too many new sessions' }, meta: {} }, { 'Retry-After': '1' })

describe('useSession', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('waits out a 429 on a new session for Retry-After and asks again until it gets one', async () => {
    const sentAt: number[] = []
    let calls = 0
    vi.stubGlobal(
      'fetch',
      vi.fn(() => {
        sentAt.push(performance.now())
        calls += 1
        return Promise.resolve(calls <= 2 ? refused() : json(201, { data: { session_id: 's-1' }, error: null, meta: {} }))
      }),
    )
    const { result } = renderHook(() => useSession(), { wrapper })

    await waitFor(() => expect(result.current.data).toEqual({ session_id: 's-1' }), { timeout: 5000 })

    expect(sentAt).toHaveLength(3)
    expect(sentAt[1]! - sentAt[0]!).toBeGreaterThanOrEqual(990)
    expect(sentAt[2]! - sentAt[1]!).toBeGreaterThanOrEqual(990)
    expect(result.current.error).toBeNull()
  })
})
