import { useQuery } from '@tanstack/react-query'
import { BookOpen, Copy, RefreshCw, Trash2 } from 'lucide-react'

import { getPages } from '../../../../../../../../shared/api/documents'
import { queryKeys } from '../../../../../../../../shared/api/queryKeys'
import type { DocumentDto } from '../../../../../../../../shared/api/types'
import { Button } from '../../../../../../../../shared/components/Button'
import { Markdown } from '../../../../../../../../shared/components/Markdown'
import { SUMMARY_MODEL_NAME } from '../../../../../../../../shared/constants/parsers'
import { useCopied } from '../../../../../../../../shared/hooks/useCopied'
import { plural } from '../../../../../../../../shared/utils/format'
import { ACTION, type CardHandlers } from '../../../../types'
import styles from './ReadyBody.module.css'

/** A `ready` card: the summary, the actions, and the start of page 1 (criteria 60, 71). */
export function ReadyBody({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  const { copied, copy } = useCopied()
  const firstPage = useQuery({
    queryKey: queryKeys.firstPage(document.id),
    queryFn: async () => (await getPages(document.id, 0, 1)).data[0] ?? null,
    staleTime: Infinity,
  })
  const summary = document.summary ?? ''

  return (
    <>
      <div className={styles.summary}>
        <div className={styles.label}>Summary · {SUMMARY_MODEL_NAME}</div>
        <Markdown source={summary} className={styles.markdown} />
      </div>
      <div className={styles.actions}>
        <Button variant="icon" aria-label={`Read the pages of ${document.filename}`} onClick={() => handlers.onOpenPages(document)}>
          <BookOpen size={22} strokeWidth={1.75} aria-hidden="true" />
        </Button>
        <Button variant="icon" aria-label={`Reparse ${document.filename}`} onClick={() => handlers.onAsk(ACTION.reparse, document)}>
          <RefreshCw size={22} strokeWidth={1.75} aria-hidden="true" />
        </Button>
        <Button variant="icon" aria-label={`Copy summary of ${document.filename}`} onClick={() => void copy(summary)}>
          <Copy size={22} strokeWidth={1.75} aria-hidden="true" />
        </Button>
        <span role="status" className={styles.copied}>
          {copied ? 'Copied' : ''}
        </span>
        <span className={styles.spacer} />
        <Button variant="icon" aria-label={`Delete ${document.filename}`} onClick={() => handlers.onAsk(ACTION.remove, document)}>
          <Trash2 size={22} strokeWidth={1.75} aria-hidden="true" />
        </Button>
      </div>
      <div className={styles.preview}>
        {firstPage.data ? (
          <p className={styles.firstPage}>
            <strong>Page 1</strong> <span>{firstPage.data.content}</span>
          </p>
        ) : null}
        <button type="button" className={styles.viewAll} onClick={() => handlers.onOpenPages(document)}>
          View all {plural(document.page_count, 'page')}
        </button>
      </div>
    </>
  )
}
