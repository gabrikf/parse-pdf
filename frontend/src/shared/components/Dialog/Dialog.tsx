import { useEffect, useRef, type CSSProperties, type ReactNode } from 'react'

import styles from './Dialog.module.css'
import { keepFocusInside } from './focusLoop'

interface DialogProps {
  open: boolean
  onClose: () => void
  labelledBy: string
  describedBy?: string
  role?: 'dialog' | 'alertdialog'
  width?: number
  /** Take the whole height the screen allows, whatever the content (the pages sheet). */
  fullHeight?: boolean
  children: ReactNode
}

/**
 * A modal on the native `<dialog>`: `showModal()` makes the page behind inert, so focus stays
 * inside (with Tab wrapping at the ends), and Escape closes it (criterion 64). On phones it docks to
 * the bottom as a sheet.
 */
export function Dialog({ open, onClose, labelledBy, describedBy, role = 'dialog', width = 560, fullHeight = false, children }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  const style = { '--dialog-width': `${width}px` } as CSSProperties
  return (
    <dialog
      ref={ref}
      className={fullHeight ? `${styles.dialog} ${styles.full}` : styles.dialog}
      style={style}
      role={role}
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      onKeyDown={keepFocusInside}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
    >
      {open ? children : null}
    </dialog>
  )
}
