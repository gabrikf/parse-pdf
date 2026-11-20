import { STATUS, type DocumentStatus } from '../api/types'

export interface StatusLook {
  label: string
  background: string
  color: string
}

/** The status pill of each status, as the canvas draws it. */
export const STATUS_LOOK: Record<DocumentStatus, StatusLook> = {
  [STATUS.queued]: { label: 'Queued', background: 'var(--surface-2)', color: 'var(--muted)' },
  [STATUS.processing]: { label: 'Processing', background: 'var(--warn-soft)', color: 'var(--warn)' },
  [STATUS.ready]: { label: 'Ready', background: 'var(--ok-soft)', color: 'var(--ok)' },
  [STATUS.noText]: { label: 'No text', background: 'var(--surface-2)', color: 'var(--text)' },
  [STATUS.dead]: { label: 'Failed', background: 'var(--danger-soft)', color: 'var(--danger)' },
  [STATUS.tooLarge]: { label: 'Too large', background: 'var(--surface-2)', color: 'var(--text)' },
}

export function isActive(status: DocumentStatus): boolean {
  return status === STATUS.queued || status === STATUS.processing
}
