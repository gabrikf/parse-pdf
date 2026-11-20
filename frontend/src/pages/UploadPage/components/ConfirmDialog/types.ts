import type { DocumentDto, ParserValue } from '../../../../shared/api/types'
import type { Action } from '../DocumentFeed/types'

/** What the page is about to do and to which document; `null` keeps the dialog closed. */
export interface ConfirmRequest {
  action: Action
  document: DocumentDto
  parser?: ParserValue
}
