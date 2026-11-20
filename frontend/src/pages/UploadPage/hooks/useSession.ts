import { useQuery } from '@tanstack/react-query'

import { isRateLimited } from '../../../shared/api/errors'
import { queryKeys } from '../../../shared/api/queryKeys'
import { openSession } from '../../../shared/api/session'

const DEFAULT_WAIT_S = 60

/**
 * Create or reuse the session before anything else is read (criterion 54). A `429` on a new
 * session (too many from one address) is waited out and asked again, never shown as the upload
 * limit, so the page loads by itself once the minute has passed.
 */
export function useSession() {
  return useQuery({
    queryKey: queryKeys.session,
    queryFn: async () => (await openSession()).data,
    staleTime: Infinity,
    retry: (failures, error) => isRateLimited(error) || failures < 1,
    retryDelay: (_, error) => (isRateLimited(error) ? (error.retryAfterSeconds ?? DEFAULT_WAIT_S) * 1000 : 1000),
  })
}
