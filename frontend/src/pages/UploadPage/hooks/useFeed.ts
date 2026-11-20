import { useInfiniteQuery } from '@tanstack/react-query'

import { listDocuments } from '../../../shared/api/documents'
import { queryKeys } from '../../../shared/api/queryKeys'
import type { FeedState } from '../../../shared/api/types'

/** The feed of one chip, newest first, 20 at a time, with the chip counts (criterion 72). */
export function useFeed(state: FeedState, enabled: boolean) {
  const query = useInfiniteQuery({
    queryKey: queryKeys.feed(state),
    queryFn: ({ pageParam }) => listDocuments(state, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.meta.next_cursor ?? null,
    enabled,
  })

  const documents = query.data?.pages.flatMap((page) => page.data) ?? []
  const counts = query.data?.pages[0]?.meta.counts
  return { ...query, documents, counts }
}
