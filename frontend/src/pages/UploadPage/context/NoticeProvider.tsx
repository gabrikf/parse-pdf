import { useCallback, useMemo, useState, type ReactNode } from 'react'

import { ApiError, UnreachableError } from '../../../shared/api/errors'
import { NoticeContext, type Notice } from './notice'

const RATE_MESSAGE: Record<string, string> = {
  rate_limited: 'Too many uploads in the last minute.',
  too_many_uploads_in_progress: 'Two uploads are still being sent.',
}

/** Holds the one notice the page shows above the feed (criterion 63). */
export function NoticeProvider({ children }: { children: ReactNode }) {
  const [notice, setNotice] = useState<Notice>(null)

  const report = useCallback((error: unknown) => {
    if (error instanceof UnreachableError) {
      setNotice({ kind: 'offline' })
      return
    }
    if (error instanceof ApiError && error.status === 429) {
      const seconds = error.retryAfterSeconds ?? 60
      const message = RATE_MESSAGE[error.code] ?? error.message
      setNotice({ kind: 'rate', until: Date.now() + seconds * 1000, message })
    }
  }, [])

  const clearOffline = useCallback(() => {
    setNotice((current) => (current?.kind === 'offline' ? null : current))
  }, [])

  const value = useMemo(() => ({ notice, report, clearOffline }), [notice, report, clearOffline])
  return <NoticeContext.Provider value={value}>{children}</NoticeContext.Provider>
}
