import { PARSER, type DocumentDto } from '../../../../../../../shared/api/types'
import { Button } from '../../../../../../../shared/components/Button'
import { NO_TEXT_HINT } from '../../../../../../../shared/constants/messages'
import { ACTION, type CardHandlers } from '../../../types'
import styles from '../DocumentCard.module.css'

/** A `no_text` card: the hint and a one-tap reparse with Gemini (criterion 61). */
export function NoTextBody({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  return (
    <div className={styles.panel}>
      <p>
        <strong>No text found on any page.</strong> {NO_TEXT_HINT}
      </p>
      <div className={styles.buttons}>
        <Button variant="primary" onClick={() => handlers.onAsk(ACTION.reparse, document, PARSER.gemini)}>
          Reparse with Gemini
        </Button>
        <Button variant="secondary" onClick={() => handlers.onAsk(ACTION.remove, document)}>
          Delete
        </Button>
      </div>
    </div>
  )
}
