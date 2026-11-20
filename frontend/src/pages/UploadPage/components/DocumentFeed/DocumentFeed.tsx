import type { DocumentDto } from '../../../../shared/api/types'
import { Button } from '../../../../shared/components/Button'
import { DocumentCard } from './components/DocumentCard'
import type { CardHandlers } from './types'

interface DocumentFeedProps {
  documents: DocumentDto[]
  handlers: CardHandlers
  hasMore: boolean
  loadingMore: boolean
  onMore: () => void
}

/** The feed column: one card per document, newest first, 20 more on demand. */
export function DocumentFeed({ documents, handlers, hasMore, loadingMore, onMore }: DocumentFeedProps) {
  return (
    <section aria-label="Documents">
      {documents.map((document) => (
        <DocumentCard key={document.id} document={document} handlers={handlers} />
      ))}
      {hasMore ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}>
          <Button variant="secondary" onClick={onMore} disabled={loadingMore}>
            {loadingMore ? 'Loading' : 'Show older documents'}
          </Button>
        </div>
      ) : null}
    </section>
  )
}
