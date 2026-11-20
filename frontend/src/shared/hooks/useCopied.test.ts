import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useCopied } from './useCopied'

function stubClipboard(writeText: (text: string) => Promise<void>) {
  vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } })
}

describe('useCopied', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('says copied, then nothing after 2 s', async () => {
    vi.useFakeTimers()
    stubClipboard(() => Promise.resolve())
    const { result } = renderHook(() => useCopied())

    await act(() => result.current.copy('# Summary'))
    expect(result.current.state).toBe('copied')
    act(() => vi.advanceTimersByTime(2000))
    expect(result.current.state).toBe('idle')
  })

  it('says it could not copy when the browser refuses, with no unhandled rejection', async () => {
    stubClipboard(() => Promise.reject(new DOMException('denied', 'NotAllowedError')))
    const { result } = renderHook(() => useCopied())

    await act(() => result.current.copy('# Summary'))
    expect(result.current.state).toBe('failed')
  })
})
