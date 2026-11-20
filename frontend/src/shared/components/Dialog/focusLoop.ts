import type { KeyboardEvent } from 'react'

const FOCUSABLE = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled]):not([tabindex="-1"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function focusables(root: HTMLElement): HTMLElement[] {
  return [...root.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((element) => element.getClientRects().length > 0)
}

/**
 * Keep Tab inside the dialog: from the last control it wraps to the first, and Shift+Tab from the
 * first wraps to the last. `showModal()` alone lets focus leave for the browser's own toolbar.
 */
export function keepFocusInside(event: KeyboardEvent<HTMLElement>): void {
  if (event.key !== 'Tab') return
  const items = focusables(event.currentTarget)
  const first = items[0]
  const last = items.at(-1)
  if (!first || !last) return

  const active = document.activeElement
  if (event.shiftKey && (active === first || active === event.currentTarget)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}
