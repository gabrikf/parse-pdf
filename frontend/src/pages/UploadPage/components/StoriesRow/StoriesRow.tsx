import { Plus } from 'lucide-react'

import { STATUS, type DocumentDto } from '../../../../shared/api/types'
import { STATUS_LOOK } from '../../../../shared/constants/statuses'
import { shortName } from '../../../../shared/utils/format'
import styles from './StoriesRow.module.css'

/** The page drawn in a story circle: Lucide's file outline with two equal lines, as the frames draw it. */
function PageGlyph() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
      <path d="M16 13H8" />
      <path d="M16 17H8" />
    </svg>
  )
}

interface StoriesRowProps {
  active: DocumentDto[]
  onUpload: () => void
  onOpen: (document: DocumentDto) => void
}

/**
 * The Upload circle and one circle per `queued` or `processing` document, its ring showing the
 * status; tapping one scrolls to its card (criterion 69). Shown once any document exists, so the
 * Upload circle stays when nothing is in progress (AD-053). Chips never filter this row.
 */
export function StoriesRow({ active, onUpload, onOpen }: StoriesRowProps) {
  return (
    <section aria-label="In progress" className={styles.row}>
      <button type="button" className={styles.story} onClick={onUpload}>
        <span className={styles.add}>
          <Plus size={24} strokeWidth={1.75} aria-hidden="true" />
        </span>
        <span className={styles.caption}>Upload</span>
      </button>
      {active.map((document) => {
        const processing = document.status === STATUS.processing
        const look = STATUS_LOOK[document.status]
        return (
          <button
            key={document.id}
            type="button"
            className={styles.story}
            aria-label={`${document.filename}, ${look.label.toLowerCase()}`}
            data-story={document.id}
            onClick={() => onOpen(document)}
          >
            <span className={`${styles.ring} ${processing ? styles.processing : styles.queued}`}>
              <span className={styles.disc}>
                <PageGlyph />
              </span>
            </span>
            <span className={styles.name}>{shortName(document.filename)}</span>
            <span className={styles.status} style={{ color: processing ? 'var(--warn)' : 'var(--muted)' }}>
              {look.label}
            </span>
          </button>
        )
      })}
    </section>
  )
}
