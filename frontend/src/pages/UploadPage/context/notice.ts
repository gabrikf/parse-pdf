import { createContext, useContext } from 'react'

export type Notice =
  | { kind: 'rate'; until: number; message: string }
  | { kind: 'offline' }
  | null

export interface NoticeApi {
  notice: Notice
  report: (error: unknown) => void
  clearOffline: () => void
}

export const NoticeContext = createContext<NoticeApi | null>(null)

/** The page-wide notice: a rate limit with its wait, or the API being unreachable. */
export function useNotice(): NoticeApi {
  const api = useContext(NoticeContext)
  if (!api) throw new Error('useNotice needs a NoticeProvider')
  return api
}
