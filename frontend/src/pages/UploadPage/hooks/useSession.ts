import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '../../../shared/api/queryKeys'
import { openSession } from '../../../shared/api/session'

/** Create or reuse the session before anything else is read (criterion 54). */
export function useSession() {
  return useQuery({
    queryKey: queryKeys.session,
    queryFn: async () => (await openSession()).data,
    staleTime: Infinity,
    retry: 1,
  })
}
