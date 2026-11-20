import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { makeDocument } from '../../../test/documents'
import { envelope, mockFetch } from '../../../test/fetchMock'
import { useActiveDocuments } from './useActiveDocuments'
import { useFeed } from './useFeed'

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

/** The active list answers each poll from `rounds`, then stays empty. */
function activeRounds(rounds: string[][]) {
  let round = 0
  return (url: string) => {
    if (!url.includes('state=active')) return envelope([], { counts: { parsed: 0, failed: 0, active: 0, all: 0 } })
    const ids = rounds[round] ?? []
    round += 1
    return envelope(ids.map((id) => makeDocument({ id })))
  }
}

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms)
  })
}

describe('useActiveDocuments', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('polls the active list every 2000 ms and stops when it is empty', async () => {
    const { calls } = mockFetch(activeRounds([['a'], ['a'], []]))
    renderHook(() => useActiveDocuments(true), { wrapper })
    const activeCalls = () => calls.filter((url) => url.includes('state=active')).length

    await advance(0)
    expect(activeCalls()).toBe(1)
    await advance(1999)
    expect(activeCalls()).toBe(1)
    await advance(1)
    expect(activeCalls()).toBe(2)
    await advance(2000)
    expect(activeCalls()).toBe(3)

    await advance(10_000)
    expect(activeCalls()).toBe(3)
    expect(calls[0]).toBe('/api/v1/documents?state=active&limit=50')
  })

  it('follows next_cursor so 51 active documents all show', async () => {
    const ids = Array.from({ length: 51 }, (_, index) => `doc-${index}`)
    const { calls } = mockFetch((url) =>
      url.includes('cursor=page-2')
        ? envelope([makeDocument({ id: 'doc-50' })], { next_cursor: null })
        : envelope(ids.slice(0, 50).map((id) => makeDocument({ id })), { next_cursor: 'page-2' }),
    )
    const { result } = renderHook(() => useActiveDocuments(true), { wrapper })

    await advance(0)

    expect(result.current.data?.map((document) => document.id)).toEqual(ids)
    expect(calls).toEqual([
      '/api/v1/documents?state=active&limit=50',
      '/api/v1/documents?state=active&limit=50&cursor=page-2',
    ])
  })

  it('refetches the feed when a document leaves the active list', async () => {
    const { calls } = mockFetch(activeRounds([['a', 'b'], ['a', 'b'], ['b']]))
    renderHook(
      () => {
        useActiveDocuments(true)
        useFeed('parsed', true)
      },
      { wrapper },
    )
    const feedCalls = () => calls.filter((url) => url.includes('state=parsed')).length

    await advance(0)
    expect(feedCalls()).toBe(1)
    await advance(2000)
    expect(feedCalls()).toBe(1)
    await advance(2000)
    await advance(50)
    expect(feedCalls()).toBe(2)
  })

  it('refetches the feed when an active document moves from queued to processing', async () => {
    let round = 0
    const { calls } = mockFetch((url) => {
      if (!url.includes('state=active')) return envelope([], { counts: { parsed: 0, failed: 0, active: 1, all: 1 } })
      round += 1
      return envelope([makeDocument({ id: 'a', status: round === 1 ? 'queued' : 'processing' })])
    })
    renderHook(
      () => {
        useActiveDocuments(true)
        useFeed('all', true)
      },
      { wrapper },
    )
    const feedCalls = () => calls.filter((url) => url.includes('state=all')).length

    await advance(0)
    expect(feedCalls()).toBe(1)
    await advance(2000)
    await advance(50)
    expect(feedCalls()).toBe(2)
  })
})
