import type { FeedState } from './types'

/** TanStack Query keys, written once. */
export const queryKeys = {
  session: ['session'] as const,
  budget: ['budget'] as const,
  documents: ['documents'] as const,
  feed: (state: FeedState) => ['documents', 'feed', state] as const,
  active: ['documents', 'active'] as const,
  pages: (id: string) => ['documents', 'pages', id] as const,
  firstPage: (id: string) => ['documents', 'first-page', id] as const,
}
