import { useEffect } from 'react'

import { useNotice } from '../context/notice'

/**
 * Hand a failed read to the notice, so an unreachable API shows its banner (criterion 63); when
 * the read succeeds again the offline banner goes away by itself.
 */
export function useReportError(error: unknown) {
  const { report, clearOffline } = useNotice()

  useEffect(() => {
    if (error) report(error)
    else clearOffline()
  }, [error, report, clearOffline])
}
