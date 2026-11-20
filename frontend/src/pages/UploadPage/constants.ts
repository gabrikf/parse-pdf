import { FEED_STATE } from '../../shared/api/types'
import type { ChipValue } from './components/FeedChips'

export const PRIVACY_NOTE = 'Files stay private to this browser and are deleted after 7 days.'

/** What an empty chip says while other chips have documents. */
export const EMPTY_CHIP: Record<ChipValue, string> = {
  [FEED_STATE.parsed]: 'No parsed documents yet. Files in progress are in the row above.',
  [FEED_STATE.failed]: 'No failed documents.',
  [FEED_STATE.all]: 'No documents yet.',
}
