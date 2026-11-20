import type { DocumentStatus } from '../../api/types'
import { STATUS_LOOK } from '../../constants/statuses'

/** The rounded status label in each card header. */
export function StatusPill({ status }: { status: DocumentStatus }) {
  const look = STATUS_LOOK[status]
  return (
    <span
      data-status={status}
      style={{
        flex: '0 0 auto',
        padding: '3px 10px',
        borderRadius: 999,
        background: look.background,
        color: look.color,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {look.label}
    </span>
  )
}
