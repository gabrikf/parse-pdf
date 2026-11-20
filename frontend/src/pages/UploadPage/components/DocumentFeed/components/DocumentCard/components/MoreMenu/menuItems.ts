import { STATUS, type DocumentDto } from '../../../../../../../../shared/api/types'
import { ACTION, type Action } from '../../../../types'

export interface MenuItem {
  label: string
  action: Action | 'pages'
  danger?: boolean
}

/** The actions each status allows (the same rules the API enforces). */
export function menuItems(document: DocumentDto): MenuItem[] {
  switch (document.status) {
    case STATUS.ready:
      return [
        { label: 'Read pages', action: 'pages' },
        { label: 'Reparse', action: ACTION.reparse },
        { label: 'Delete forever', action: ACTION.remove, danger: true },
      ]
    case STATUS.noText:
      return [
        { label: 'Reparse', action: ACTION.reparse },
        { label: 'Delete forever', action: ACTION.remove, danger: true },
      ]
    case STATUS.dead:
      return [
        { label: 'Retry', action: ACTION.requeue },
        { label: 'Reparse with another parser', action: ACTION.reparse },
        { label: 'Delete forever', action: ACTION.remove, danger: true },
      ]
    case STATUS.tooLarge:
    case STATUS.queued:
      return [{ label: 'Delete forever', action: ACTION.remove, danger: true }]
    default:
      return []
  }
}
