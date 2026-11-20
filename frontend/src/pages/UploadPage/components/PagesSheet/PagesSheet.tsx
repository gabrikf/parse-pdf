import { useInfiniteQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'

import { getPages, PAGES_PAGE_SIZE } from '../../../../shared/api/documents'
import { queryKeys } from '../../../../shared/api/queryKeys'
import type { DocumentDto, PageDto } from '../../../../shared/api/types'
import { Button } from '../../../../shared/components/Button'
import { Dialog } from '../../../../shared/components/Dialog'
import { Markdown } from '../../../../shared/components/Markdown'
import { parserName } from '../../../../shared/constants/parsers'
import { formatCount, plural } from '../../../../shared/utils/format'
import styles from './PagesSheet.module.css'

function PageBody({ page }: { page: PageDto }) {
  if (page.format === 'markdown') return <Markdown source={page.content} className={styles.markdown} />
  return <p className={styles.text}>{page.content}</p>
}

/** A ready document's pages, 50 at a time, with a control for the next 50 (criterion 60). */
export function PagesSheet({ document, onClose }: { document: DocumentDto | null; onClose: () => void }) {
  const pages = useInfiniteQuery({
    queryKey: queryKeys.pages(document?.id ?? ''),
    queryFn: ({ pageParam }) => getPages(document?.id ?? '', pageParam),
    initialPageParam: 0,
    getNextPageParam: (last, all) => {
      const loaded = all.reduce((sum, page) => sum + page.data.length, 0)
      return loaded < (last.meta.total ?? 0) ? loaded : undefined
    },
    enabled: document !== null,
  })
  const list = pages.data?.pages.flatMap((page) => page.data) ?? []
  const total = pages.data?.pages[0]?.meta.total ?? document?.page_count ?? 0
  const format = list[0]?.format ?? 'text'

  return (
    <Dialog open={document !== null} onClose={onClose} labelledBy="pages-title" width={680}>
      <header className={styles.header}>
        <div className={styles.titles}>
          <h2 id="pages-title" className={styles.title}>
            {document?.filename}
          </h2>
          <div className={styles.meta}>
            {plural(total, 'page')} · {format} · {document ? parserName(document.parser) : ''}
          </div>
        </div>
        <Button variant="icon" aria-label="Close pages" onClick={onClose}>
          <X size={22} aria-hidden="true" />
        </Button>
      </header>
      <div className={styles.body}>
        {list.map((page) => (
          <article key={page.number} aria-label={`Page ${page.number}`} className={styles.page}>
            <div className={styles.number}>Page {page.number}</div>
            <PageBody page={page} />
          </article>
        ))}
        <div className={styles.footer}>
          <span role="status">
            Showing {formatCount(list.length)} of {plural(total, 'page')}
          </span>
          {pages.hasNextPage ? (
            <Button variant="secondary" disabled={pages.isFetchingNextPage} onClick={() => void pages.fetchNextPage()}>
              {pages.isFetchingNextPage ? 'Loading' : `Load the next ${PAGES_PAGE_SIZE} pages`}
            </Button>
          ) : null}
        </div>
      </div>
    </Dialog>
  )
}
