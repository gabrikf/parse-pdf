import { Ellipsis } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'

import type { DocumentDto } from '../../../../../../../../shared/api/types'
import { Button } from '../../../../../../../../shared/components/Button'
import type { CardHandlers } from '../../../../types'
import { menuItems, type MenuItem } from './menuItems'
import styles from './MoreMenu.module.css'

/**
 * The "..." button of a card: a disclosure that shows the actions its status allows as plain
 * buttons, reached with Tab. Escape or a click outside closes it; Escape puts focus back on "...".
 */
export function MoreMenu({ document, handlers }: { document: DocumentDto; handlers: CardHandlers }) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const menuId = useId()
  const items = menuItems(document)

  useEffect(() => {
    if (!open) return undefined
    const close = (event: Event) => {
      if (event instanceof KeyboardEvent) {
        if (event.key !== 'Escape') return
        wrap.current?.querySelector('button')?.focus()
        setOpen(false)
      } else if (!wrap.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    window.addEventListener('pointerdown', close)
    window.addEventListener('keydown', close)
    return () => {
      window.removeEventListener('pointerdown', close)
      window.removeEventListener('keydown', close)
    }
  }, [open])

  const pick = (item: MenuItem) => {
    // The picked button unmounts with the list: move focus to "..." first, so the dialog it opens
    // gives focus back there when it closes.
    wrap.current?.querySelector('button')?.focus()
    setOpen(false)
    if (item.action === 'pages') handlers.onOpenPages(document)
    else handlers.onAsk(item.action, document)
  }

  return (
    <div className={styles.wrap} ref={wrap}>
      <Button
        variant="icon"
        aria-label={`More actions for ${document.filename}`}
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        disabled={items.length === 0}
        onClick={() => setOpen((value) => !value)}
      >
        <Ellipsis size={22} strokeWidth={2} aria-hidden="true" />
      </Button>
      {open ? (
        <ul id={menuId} aria-label={`Actions for ${document.filename}`} className={styles.menu}>
          {items.map((item) => (
            <li key={item.label}>
              <button type="button" className={`${styles.item} ${item.danger ? styles.danger : ''}`} onClick={() => pick(item)}>
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
