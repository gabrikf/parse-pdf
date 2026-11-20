import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '../../../shared/api/queryKeys'
import { getBudget } from '../../../shared/api/session'

/** Today's model page budget from `GET /api/v1/budget` (criterion 70). */
export function useBudget(enabled: boolean) {
  return useQuery({ queryKey: queryKeys.budget, queryFn: async () => (await getBudget()).data, enabled })
}
