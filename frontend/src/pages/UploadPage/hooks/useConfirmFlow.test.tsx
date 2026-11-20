import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ACTION_ERROR } from '../../../shared/constants/messages'
import { makeDocument } from '../../../test/documents'
import { ACTION } from '../components/DocumentFeed/types'
import { NoticeProvider } from '../context/NoticeProvider'
import { useConfirmFlow } from './useConfirmFlow'

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <NoticeProvider>{children}</NoticeProvider>
    </QueryClientProvider>
  )
}

function answer(status: number, code?: string) {
  const body = code ? { data: null, error: { code, message: code }, meta: {} } : { data: { id: 'x' }, error: null, meta: {} }
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

/** Every fetch waits until the test answers it, in the order they were sent. */
function holdFetch() {
  const held: { url: string; method: string; reply: (response: Response) => void }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(
      (input: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((resolve) => held.push({ url: String(input), method: init?.method ?? 'GET', reply: resolve })),
    ),
  )
  return held
}

const a = makeDocument({ id: 'a', filename: 'a.pdf', status: 'ready' })
const b = makeDocument({ id: 'b', filename: 'b.pdf', status: 'dead' })

describe('useConfirmFlow', () => {
  afterEach(() => vi.unstubAllGlobals())

  it("keeps a cancelled confirmation's answer away from the one opened after it", async () => {
    const held = holdFetch()
    const { result } = renderHook(() => useConfirmFlow(), { wrapper })

    act(() => result.current.ask({ action: ACTION.remove, document: a }))
    act(() => result.current.confirm({ action: ACTION.remove, document: a }))
    act(() => result.current.cancel())
    act(() => result.current.ask({ action: ACTION.requeue, document: b }))
    act(() => result.current.confirm({ action: ACTION.requeue, document: b }))
    expect(held.map((call) => `${call.method} ${call.url}`)).toEqual(['DELETE /api/v1/documents/a', 'POST /api/v1/documents/b/requeue'])

    await act(async () => held[0]?.reply(answer(409, 'document_busy')))
    expect(result.current.asking?.document.id).toBe('b')
    expect(result.current.error).toBeNull()
    expect(result.current.pending).toBe(true)

    await act(async () => held[1]?.reply(answer(202)))
    expect(result.current.asking).toBeNull()
  })

  it('sends one request for a double click', () => {
    const held = holdFetch()
    const { result } = renderHook(() => useConfirmFlow(), { wrapper })

    act(() => {
      result.current.ask({ action: ACTION.remove, document: a })
    })
    act(() => {
      result.current.confirm({ action: ACTION.remove, document: a })
      result.current.confirm({ action: ACTION.remove, document: a })
    })
    expect(held).toHaveLength(1)
  })

  it.each([
    [409, 'document_busy'],
    [409, 'not_dead'],
    [404, 'document_not_found'],
    [429, 'model_budget_exhausted'],
  ])('a %i %s keeps the confirmation open with its reason', async (status, code) => {
    const held = holdFetch()
    const { result } = renderHook(() => useConfirmFlow(), { wrapper })

    act(() => result.current.ask({ action: ACTION.requeue, document: b }))
    act(() => result.current.confirm({ action: ACTION.requeue, document: b }))
    await act(async () => held[0]?.reply(answer(status, code)))

    expect(result.current.asking?.document.id).toBe('b')
    expect(result.current.error).toBe(ACTION_ERROR[code])
    expect(result.current.pending).toBe(false)
  })
})
