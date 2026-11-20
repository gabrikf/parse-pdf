import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'

import { queryKeys } from './queryKeys'
import { refreshDocuments } from './refreshDocuments'

describe('refreshDocuments', () => {
  it('marks the lists and the budget stale but never a page-1 preview', async () => {
    const client = new QueryClient()
    const keys = [queryKeys.feed('all'), queryKeys.active, queryKeys.pages('a', 't1'), queryKeys.budget, queryKeys.firstPage('a', 't1')]
    for (const key of keys) client.setQueryData(key, 'cached')

    await refreshDocuments(client)

    const stale = keys.map((key) => client.getQueryState(key)?.isInvalidated)
    expect(stale).toEqual([true, true, true, true, false])
  })
})
