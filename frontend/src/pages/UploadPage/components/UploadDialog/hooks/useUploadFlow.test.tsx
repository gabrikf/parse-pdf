import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { NoticeProvider } from '../../../context/NoticeProvider'
import { useUploadFlow } from './useUploadFlow'

function wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <NoticeProvider>{children}</NoticeProvider>
    </QueryClientProvider>
  )
}

describe('useUploadFlow', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('ignores the answer of a batch sent before the dialog was closed', async () => {
    const held: ((response: Response) => void)[] = []
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>((resolve) => held.push(resolve))))
    const { result } = renderHook(() => useUploadFlow(), { wrapper })

    act(() => result.current.add([new File(['%PDF-1.7'], 'a.pdf', { type: 'application/pdf' })]))
    let sent: Promise<void> = Promise.resolve()
    act(() => {
      sent = result.current.submit('pypdf')
    })
    act(() => result.current.reset())
    const refused = { data: null, error: { code: 'rate_limited', message: 'Too many uploads' }, meta: {} }
    await act(async () => {
      held[0]?.(new Response(JSON.stringify(refused), { status: 429, headers: { 'Content-Type': 'application/json' } }))
      await sent
    })

    expect(result.current.error).toBeNull()
    expect(result.current.files).toEqual([])
  })
})
