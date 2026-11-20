import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import type { DocumentDto } from '../../shared/api/types'
import { FEED_STATE } from '../../shared/api/types'
import { useTheme } from '../../shared/hooks/useTheme'
import { ConfirmDialog, type ConfirmRequest } from './components/ConfirmDialog'
import { DocumentFeed } from './components/DocumentFeed'
import { ACTION, type CardHandlers } from './components/DocumentFeed/types'
import { EmptyChip, EmptyFeed } from './components/EmptyFeed'
import { FeedChips, type ChipValue } from './components/FeedChips'
import { Notices } from './components/Notices'
import { PagesSheet } from './components/PagesSheet'
import { RightRail } from './components/RightRail'
import { SideRail } from './components/SideRail'
import { StoriesRow } from './components/StoriesRow'
import { TabBar } from './components/TabBar'
import { TopBar } from './components/TopBar'
import { UploadDialog } from './components/UploadDialog'
import { EMPTY_CHIP } from './constants'
import { useNotice } from './context/notice'
import { useActiveDocuments } from './hooks/useActiveDocuments'
import { useBudget } from './hooks/useBudget'
import { useDocumentActions } from './hooks/useDocumentActions'
import { useFeed } from './hooks/useFeed'
import { useReportError } from './hooks/useReportError'
import { useSession } from './hooks/useSession'
import { useStoryScroll } from './hooks/useStoryScroll'
import styles from './UploadPage.module.css'

/** The one page: stories row, chips and feed, with the upload, pages and confirm dialogs. */
export function UploadPage() {
  const client = useQueryClient()
  const { clearOffline } = useNotice()
  const { theme, toggle } = useTheme()
  const [chip, setChip] = useState<ChipValue>(FEED_STATE.parsed)
  const [uploading, setUploading] = useState(false)
  const [reading, setReading] = useState<DocumentDto | null>(null)
  const [asking, setAsking] = useState<ConfirmRequest | null>(null)

  const session = useSession()
  const ready = session.isSuccess
  const feed = useFeed(chip, ready)
  const active = useActiveDocuments(ready)
  const budget = useBudget(ready)
  const actions = useDocumentActions()
  const openStory = useStoryScroll(feed.documents, () => setChip(FEED_STATE.all))

  useReportError(session.error)
  useReportError(feed.error)
  useReportError(active.error)
  useReportError(budget.error)

  const activeDocuments = active.data ?? []
  const nothingYet = ready && feed.counts?.all === 0 && activeDocuments.length === 0
  const handlers: CardHandlers = {
    onOpenPages: setReading,
    onAsk: (action, document, parser) => setAsking(parser ? { action, document, parser } : { action, document }),
  }

  const retry = () => {
    clearOffline()
    void client.refetchQueries({ type: 'active' })
  }

  const confirm = (request: ConfirmRequest) => {
    setAsking(null)
    const { id } = request.document
    if (request.action === ACTION.reparse && request.parser) actions.reparse.mutate({ id, parser: request.parser })
    if (request.action === ACTION.requeue) actions.requeue.mutate(id)
    if (request.action === ACTION.remove) actions.remove.mutate(id)
  }

  const showFeed = () => window.scrollTo({ top: 0 })
  const openUpload = () => setUploading(true)

  return (
    <div className={styles.shell}>
      <SideRail theme={theme} onToggleTheme={toggle} onUpload={openUpload} onFeed={showFeed} />
      <TopBar budget={budget.data} />
      <main className={styles.main}>
        <div className={styles.column}>
          <h1 className="visually-hidden">Your documents</h1>
          <Notices onRetry={retry} />
          {activeDocuments.length > 0 ? <StoriesRow active={activeDocuments} onUpload={openUpload} onOpen={openStory} /> : null}
          {nothingYet ? (
            <EmptyFeed onUpload={openUpload} />
          ) : (
            <>
              <FeedChips value={chip} counts={feed.counts} onChange={setChip} />
              {feed.isSuccess && feed.documents.length === 0 ? <EmptyChip label={EMPTY_CHIP[chip]} /> : null}
              <DocumentFeed
                documents={feed.documents}
                handlers={handlers}
                hasMore={feed.hasNextPage}
                loadingMore={feed.isFetchingNextPage}
                onMore={() => void feed.fetchNextPage()}
              />
            </>
          )}
        </div>
        <RightRail budget={budget.data} />
      </main>
      <TabBar theme={theme} onToggleTheme={toggle} onUpload={openUpload} onFeed={showFeed} />
      <UploadDialog open={uploading} onClose={() => setUploading(false)} />
      <PagesSheet document={reading} onClose={() => setReading(null)} />
      <ConfirmDialog request={asking} onCancel={() => setAsking(null)} onConfirm={confirm} />
    </div>
  )
}
