import { ACTION } from '../DocumentFeed/types'
import { parserName } from '../../../../shared/constants/parsers'
import type { ConfirmRequest } from './types'

interface ConfirmCopy {
  title: string
  body: string
  confirm: string
}

/** The canvas copy of each confirmation, naming the file (criterion 62). */
export function confirmCopy({ action, document }: ConfirmRequest): ConfirmCopy {
  if (action === ACTION.reparse) {
    return {
      title: `Reparse ${document.filename}?`,
      body: 'Its pages and summary are cleared, then it runs again with the parser you pick.',
      confirm: 'Reparse',
    }
  }
  if (action === ACTION.requeue) {
    return {
      title: `Retry ${document.filename}?`,
      body: `It goes back in the queue with the same parser, ${parserName(document.parser)}.`,
      confirm: 'Retry',
    }
  }
  return {
    title: `Delete ${document.filename} forever?`,
    body: "The PDF, its pages and its summary are removed for good. This can't be undone.",
    confirm: 'Delete forever',
  }
}
