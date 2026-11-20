import { FileText } from 'lucide-react'

import { STATUS, type DocumentDto } from '../../../../../../shared/api/types'
import { StatusPill } from '../../../../../../shared/components/StatusPill'
import type { CardHandlers } from '../../types'
import { BusyBody } from './components/BusyBody'
import { DeadBody } from './components/DeadBody'
import { MoreMenu } from './components/MoreMenu'
import { NoTextBody } from './components/NoTextBody'
import { ReadyBody } from './components/ReadyBody'
import { TooLargeBody } from './components/TooLargeBody'
import styles from './DocumentCard.module.css'
import { cardMeta } from './utils'

/** One post of the feed: header with status, then the body its status calls for. */
export function DocumentCard({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  return (
    <article id={`doc-${document.id}`} aria-label={document.filename} className={styles.card} data-status={document.status}>
      <header className={styles.header}>
        <span className={styles.avatar}>
          <FileText size={20} strokeWidth={1.75} aria-hidden="true" />
        </span>
        <div className={styles.titles}>
          <h2 className={styles.name}>{document.filename}</h2>
          <div className={styles.meta}>{cardMeta(document)}</div>
        </div>
        <StatusPill status={document.status} />
        <MoreMenu document={document} handlers={handlers} />
      </header>
      <CardBody document={document} handlers={handlers} />
    </article>
  )
}

function CardBody({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  switch (document.status) {
    case STATUS.ready:
      return <ReadyBody document={document} handlers={handlers} />
    case STATUS.noText:
      return <NoTextBody document={document} handlers={handlers} />
    case STATUS.dead:
      return <DeadBody document={document} handlers={handlers} />
    case STATUS.tooLarge:
      return <TooLargeBody document={document} handlers={handlers} />
    default:
      return <BusyBody document={document} />
  }
}
