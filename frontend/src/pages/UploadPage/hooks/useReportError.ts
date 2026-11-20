import { useEffect } from 'react'

import { useNotice } from '../context/notice'

/** Hand a failed read to the notice, so an unreachable API shows its banner (criterion 63). */
export function useReportError(error: unknown) {
  const { report } = useNotice()

  useEffect(() => {
    if (error) report(error)
  }, [error, report])
}
