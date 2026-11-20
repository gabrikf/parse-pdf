import type { FeedState } from './types'

/** TanStack Query keys, written once. */
export const queryKeys = {
  session: ['session'] as const,
  budget: ['budget'] as const,
  documents: ['documents'] as const,
  feed: (state: FeedState) => ['documents', 'feed', state] as const,
  active: ['documents', 'active'] as const,
  pages: (id: string) => ['documents', 'pages', id] as const,
  /** Keyed by `updated_at` too, so a reparsed document never reuses the old parser's page 1. */
  firstPage: (id: string, updatedAt: string) => ['documents', 'first-page', id, updatedAt] as const,
}
