import { useCallback, useEffect, useRef, useState } from 'react'

import { COPIED_FOR_MS } from '../constants/limits'

export type CopyState = 'idle' | 'copied' | 'failed'

/**
 * Copy text to the clipboard and say "Copied" for 2 s (criterion 71). Where the browser refuses
 * (no clipboard over plain http, or permission denied) it says so for the same 2 s.
 */
export function useCopied(): { state: CopyState; copy: (text: string) => Promise<void> } {
  const [state, setState] = useState<CopyState>('idle')
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const copy = useCallback(async (text: string) => {
    let outcome: CopyState = 'copied'
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      outcome = 'failed'
    }
    setState(outcome)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setState('idle'), COPIED_FOR_MS)
  }, [])

  return { state, copy }
}
