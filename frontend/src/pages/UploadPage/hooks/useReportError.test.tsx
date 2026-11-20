import { renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'

import { UnreachableError } from '../../../shared/api/errors'
import { useNotice } from '../context/notice'
import { NoticeProvider } from '../context/NoticeProvider'
import { useReportError } from './useReportError'

function wrapper({ children }: { children: ReactNode }) {
  return <NoticeProvider>{children}</NoticeProvider>
}

describe('useReportError', () => {
  it('shows the offline banner while a read fails and clears it when the read succeeds again', () => {
    const { result, rerender } = renderHook(
      ({ error }: { error: unknown }) => {
        useReportError(error)
        return useNotice().notice
      },
      { wrapper, initialProps: { error: new UnreachableError() as unknown } },
    )
    expect(result.current).toEqual({ kind: 'offline' })

    rerender({ error: null })
    expect(result.current).toBeNull()
  })
})
