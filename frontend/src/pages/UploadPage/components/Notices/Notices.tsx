import { TriangleAlert } from 'lucide-react'
import { useState } from 'react'

import { useCountdown } from '../../../../shared/hooks/useCountdown'
import { useNotice } from '../../context/notice'
import styles from './Notices.module.css'

interface RateProps {
  until: number
  message: string
}

/** The wait after a 429, ticking on screen; mounted once per limit, so the clock starts with it. */
function RateNotice({ until, message }: RateProps) {
  const seconds = useCountdown(until)
  if (seconds <= 0) return null
  return (
    <div className={styles.rate}>
      <TriangleAlert size={18} strokeWidth={2} aria-hidden="true" />
      <span>
        {message} You can upload again in {seconds} s.
      </span>
    </div>
  )
}

/** What a screen reader hears about the wait: once when it starts and once when it ends, not every
 * second. Its text changes only at those two moments. */
function RateAnnouncement({ until, message }: RateProps) {
  const [wait] = useState(() => Math.max(1, Math.ceil((until - Date.now()) / 1000)))
  const seconds = useCountdown(until)
  return <>{seconds > 0 ? `${message} You can upload again in ${wait} seconds.` : 'You can upload again.'}</>
}

/** The rate-limit wait and the unreachable-API banner above the feed (criterion 63). */
export function Notices({ onRetry }: { onRetry: () => void }) {
  const { notice } = useNotice()
  const rate = notice?.kind === 'rate' ? notice : null

  return (
    <>
      <span role="status" className="visually-hidden">
        {rate ? <RateAnnouncement key={rate.until} until={rate.until} message={rate.message} /> : null}
      </span>
      {notice?.kind === 'offline' ? (
        <div role="alert" className={styles.offline}>
          <span>Can&apos;t reach the server. Your files are safe; the feed will refresh when it&apos;s back.</span>
          <button type="button" className={styles.retry} onClick={onRetry}>
            Retry
          </button>
        </div>
      ) : null}
      {rate ? <RateNotice key={rate.until} until={rate.until} message={rate.message} /> : null}
    </>
  )
}
