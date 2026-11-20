import type { DocumentDto } from '../../../../../../../shared/api/types'
import { Button } from '../../../../../../../shared/components/Button'
import { deadReason } from '../../../../../../../shared/constants/messages'
import { ACTION, type CardHandlers } from '../../../types'
import styles from '../DocumentCard.module.css'

/** A `dead` card: why (the API's hint names the tries and the last cause), then Retry, Reparse with another parser, Delete forever (criterion 73). */
export function DeadBody({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  return (
    <div className={`${styles.panel} ${styles.danger}`}>
      <p>{document.hint ?? deadReason(document.error_code)}</p>
      <div className={styles.buttons}>
        <Button variant="primary" onClick={() => handlers.onAsk(ACTION.requeue, document)}>
          Retry
        </Button>
        <Button variant="raised" onClick={() => handlers.onAsk(ACTION.reparse, document)}>
          Reparse with another parser
        </Button>
        <Button variant="dangerOutline" onClick={() => handlers.onAsk(ACTION.remove, document)}>
          Delete forever
        </Button>
      </div>
    </div>
  )
}
