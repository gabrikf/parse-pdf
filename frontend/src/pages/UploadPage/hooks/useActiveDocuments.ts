import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { ACTIVE_PAGE_SIZE, listDocuments } from '../../../shared/api/documents'
import { queryKeys } from '../../../shared/api/queryKeys'
import { FEED_STATE } from '../../../shared/api/types'
import { POLL_INTERVAL_MS } from '../../../shared/constants/limits'

/**
 * The `queued` and `processing` documents, polled every 2,000 ms while the list is not empty
 * (criterion 59). When a document leaves the list the feed, its counts and the budget refetch.
 */
export function useActiveDocuments(enabled: boolean) {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: queryKeys.active,
    queryFn: async () => (await listDocuments(FEED_STATE.active, null, ACTIVE_PAGE_SIZE)).data,
    enabled,
    refetchInterval: (current) => ((current.state.data?.length ?? 0) > 0 ? POLL_INTERVAL_MS : false),
    refetchIntervalInBackground: true,
  })

  const previous = useRef<Set<string>>(new Set())
  useEffect(() => {
    if (!query.data) return
    const now = new Set(query.data.map((document) => document.id))
    const left = [...previous.current].some((id) => !now.has(id))
    previous.current = now
    if (left) {
      void client.invalidateQueries({ queryKey: ['documents', 'feed'] })
      void client.invalidateQueries({ queryKey: queryKeys.budget })
    }
  }, [query.data, client])

  return query
}
