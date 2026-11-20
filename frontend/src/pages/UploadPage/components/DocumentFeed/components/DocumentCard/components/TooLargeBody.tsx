import type { DocumentDto } from '../../../../../../../shared/api/types'
import { Button } from '../../../../../../../shared/components/Button'
import { ACTION, type CardHandlers } from '../../../types'
import styles from '../DocumentCard.module.css'
import { tooLargeReason } from '../utils'

/** A `too_large` card: the limit it passed and only Delete forever (criterion 73). */
export function TooLargeBody({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  return (
    <div className={`${styles.panel} ${styles.tooLarge}`}>
      <p>{tooLargeReason(document)}</p>
      <Button variant="dangerOutline" style={{ background: 'transparent' }} onClick={() => handlers.onAsk(ACTION.remove, document)}>
        Delete forever
      </Button>
    </div>
  )
}
