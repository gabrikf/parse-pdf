import { useCallback, useEffect, useRef, useState } from 'react'

import { COPIED_FOR_MS } from '../constants/limits'

/** Copy text to the clipboard and say "Copied" for 2 s (criterion 71). */
export function useCopied(): { copied: boolean; copy: (text: string) => Promise<void> } {
  const [copied, setCopied] = useState(false)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setCopied(false), COPIED_FOR_MS)
  }, [])

  return { copied, copy }
}
