import { STATUS, type DocumentDto } from '../../../../../../shared/api/types'
import { MAX_FILE_BYTES } from '../../../../../../shared/constants/limits'
import { parserName } from '../../../../../../shared/constants/parsers'
import { formatBytes, plural, timeAgo } from '../../../../../../shared/utils/format'

/** `Gemini 3.1 Flash Lite · 18 pages · 3 min ago`; a too-large file shows its size instead. */
export function cardMeta(document: DocumentDto, now: number = Date.now()): string {
  const amount =
    document.status === STATUS.tooLarge && document.size_bytes > MAX_FILE_BYTES
      ? formatBytes(document.size_bytes)
      : plural(document.page_count, 'page')
  return `${parserName(document.parser)} · ${amount} · ${timeAgo(document.created_at, now)}`
}

/** Why a file is too large, in the canvas's words. */
export function tooLargeReason(document: DocumentDto): string {
  if (document.size_bytes > MAX_FILE_BYTES) {
    return `${formatBytes(document.size_bytes)} is over the 50 MB limit, so it can't be retried. Split or compress the PDF, then upload it again.`
  }
  return `${plural(document.page_count, 'page')} is over the 1,000-page limit, so it can't be retried. Split the PDF, then upload it again.`
}
