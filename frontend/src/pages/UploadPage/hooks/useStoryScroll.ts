import { useEffect, useRef } from 'react'

import type { DocumentDto } from '../../../shared/api/types'

function scrollToCard(id: string): boolean {
  const card = document.getElementById(`doc-${id}`)
  if (!card) return false
  card.scrollIntoView({ block: 'start' })
  return true
}

/**
 * Tapping a story scrolls to its card (criterion 69). An active document is only in the "All"
 * feed, so the page may switch chips first; the scroll then waits for the card to render.
 */
export function useStoryScroll(documents: DocumentDto[], showAll: () => void) {
  const target = useRef<string | null>(null)

  useEffect(() => {
    if (target.current && scrollToCard(target.current)) target.current = null
  }, [documents])

  return (document: DocumentDto) => {
    if (scrollToCard(document.id)) return
    target.current = document.id
    showAll()
  }
}
