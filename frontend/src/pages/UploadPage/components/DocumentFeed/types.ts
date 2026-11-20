import type { DocumentDto, ParserValue } from '../../../../shared/api/types'

export const ACTION = { reparse: 'reparse', requeue: 'requeue', remove: 'remove' } as const

export type Action = (typeof ACTION)[keyof typeof ACTION]

/** What a card asks the page to do; the page confirms before sending (criterion 62). */
export interface CardHandlers {
  onOpenPages: (document: DocumentDto) => void
  onAsk: (action: Action, document: DocumentDto, parser?: ParserValue) => void
}
