import { act, cleanup, render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../../../shared/api/errors'
import { useNotice } from '../../context/notice'
import { NoticeProvider } from '../../context/NoticeProvider'
import { Notices } from './Notices'

function RateLimited({ seconds }: { seconds: number }) {
  const { report } = useNotice()
  useEffect(() => report(new ApiError(429, 'rate_limited', 'rate limited', seconds)), [report, seconds])
  return null
}

describe('Notices', () => {
  afterEach(() => {
    cleanup()
    vi.useRealTimers()
  })

  it('announces the wait when it starts and when it ends, and nothing in between', async () => {
    vi.useFakeTimers()
    render(
      <NoticeProvider>
        <RateLimited seconds={3} />
        <Notices onRetry={() => undefined} />
      </NoticeProvider>,
    )
    const live = screen.getByRole('status')
    const start = 'Too many uploads in the last minute. You can upload again in 3 seconds.'
    expect(live).toHaveTextContent(start)
    expect(screen.getByText(/You can upload again in 3 s\.$/)).toBeVisible()

    await act(async () => vi.advanceTimersByTimeAsync(1000))
    expect(screen.getByText(/You can upload again in 2 s\.$/)).toBeVisible()
    expect(live).toHaveTextContent(start)

    await act(async () => vi.advanceTimersByTimeAsync(2000))
    expect(live).toHaveTextContent(/^You can upload again\.$/)
    expect(screen.queryByText(/You can upload again in \d+ s\./)).toBeNull()
  })
})
