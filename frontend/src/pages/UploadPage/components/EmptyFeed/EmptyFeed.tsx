import { CloudUpload } from 'lucide-react'

import { Button } from '../../../../shared/components/Button'
import { PRIVACY_NOTE } from '../../constants'
import styles from './EmptyFeed.module.css'

/** The first visit: no documents yet, and the way to upload (criterion 54). */
export function EmptyFeed({ onUpload }: { onUpload: () => void }) {
  return (
    <section className={styles.empty} aria-label="No documents">
      <span className={styles.icon}>
        <CloudUpload size={32} strokeWidth={1.75} aria-hidden="true" />
      </span>
      <h2 className={styles.title}>No documents yet</h2>
      <p className={styles.text}>Upload a PDF to read it page by page, with a short summary at the top.</p>
      <Button variant="primary" onClick={onUpload}>
        Upload PDFs
      </Button>
      <p className={styles.note}>{PRIVACY_NOTE}</p>
    </section>
  )
}

/** A chip with nothing in it, while other chips have documents. */
export function EmptyChip({ label }: { label: string }) {
  return <p className={styles.quiet}>{label}</p>
}
