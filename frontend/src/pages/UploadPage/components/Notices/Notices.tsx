import { TriangleAlert } from 'lucide-react'

import { useCountdown } from '../../../../shared/hooks/useCountdown'
import { useNotice } from '../../context/notice'
import styles from './Notices.module.css'

/** The wait after a 429; mounted once per limit, so the clock starts when the limit arrives. */
function RateNotice({ until, message }: { until: number; message: string }) {
  const seconds = useCountdown(until)
  if (seconds <= 0) return null
  return (
    <div role="status" className={styles.rate}>
      <TriangleAlert size={18} strokeWidth={2} aria-hidden="true" />
      <span>
        {message} You can upload again in {seconds} s.
      </span>
    </div>
  )
}

/** The rate-limit wait and the unreachable-API banner above the feed (criterion 63). */
export function Notices({ onRetry }: { onRetry: () => void }) {
  const { notice } = useNotice()

  if (notice?.kind === 'offline') {
    return (
      <div role="alert" className={styles.offline}>
        <span>Can&apos;t reach the server. Your files are safe; the feed will refresh when it&apos;s back.</span>
        <button type="button" className={styles.retry} onClick={onRetry}>
          Retry
        </button>
      </div>
    )
  }
  if (notice?.kind === 'rate') return <RateNotice key={notice.until} until={notice.until} message={notice.message} />
  return null
}
