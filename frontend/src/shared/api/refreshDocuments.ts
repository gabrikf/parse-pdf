import type { QueryClient } from '@tanstack/react-query'

import { queryKeys } from './queryKeys'

/**
 * Refetch the lists and the budget after a change. A card's page-1 preview is left alone: its key
 * carries `updated_at` and never goes stale, and refetching it would send one request per card.
 */
export async function refreshDocuments(client: QueryClient): Promise<void> {
  await client.invalidateQueries({
    queryKey: queryKeys.documents,
    predicate: (query) => query.queryKey[1] !== 'first-page',
  })
  await client.invalidateQueries({ queryKey: queryKeys.budget })
}
