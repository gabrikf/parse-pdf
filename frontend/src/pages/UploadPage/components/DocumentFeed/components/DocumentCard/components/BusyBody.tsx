import { STATUS, type DocumentDto } from '../../../../../../../shared/api/types'
import { parserName } from '../../../../../../../shared/constants/parsers'
import styles from '../DocumentCard.module.css'

/** A `queued` or `processing` card: placeholder lines and what is happening. */
export function BusyBody({ document }: { document: DocumentDto }) {
  const text =
    document.status === STATUS.queued
      ? 'Waiting for a worker. Pages and a summary appear here when it finishes.'
      : `Reading pages with ${parserName(document.parser)}. The summary appears here when it finishes.`
  return (
    <div className={`${styles.panel} ${styles.busy}`}>
      <div className={styles.bar} style={{ width: '78%' }} />
      <div className={styles.bar} style={{ width: '92%' }} />
      <div className={styles.bar} style={{ width: '64%' }} />
      <p className={styles.busyText}>{text}</p>
    </div>
  )
}
