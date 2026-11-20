import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { ACTIVE_PAGE_SIZE, listAllDocuments } from '../../../shared/api/documents'
import { queryKeys } from '../../../shared/api/queryKeys'
import { FEED_STATE } from '../../../shared/api/types'
import { POLL_INTERVAL_MS } from '../../../shared/constants/limits'

/**
 * Every `queued` and `processing` document (all pages, not only the first 50), polled every
 * 2,000 ms while the list is not empty (criteria 59 and 72). When a document leaves the list or
 * changes status (`queued` to `processing`), the feed, its counts and the budget refetch.
 */
export function useActiveDocuments(enabled: boolean) {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: queryKeys.active,
    queryFn: () => listAllDocuments(FEED_STATE.active, ACTIVE_PAGE_SIZE),
    enabled,
    refetchInterval: (current) => ((current.state.data?.length ?? 0) > 0 ? POLL_INTERVAL_MS : false),
    refetchIntervalInBackground: true,
  })

  const previous = useRef<Set<string>>(new Set())
  useEffect(() => {
    if (!query.data) return
    const now = new Set(query.data.map((document) => `${document.id}:${document.status}`))
    const changed = [...previous.current].some((seen) => !now.has(seen))
    previous.current = now
    if (changed) {
      void client.invalidateQueries({ queryKey: ['documents', 'feed'] })
      void client.invalidateQueries({ queryKey: queryKeys.budget })
    }
  }, [query.data, client])

  return query
}
