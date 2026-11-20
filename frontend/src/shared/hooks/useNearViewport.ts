import { useEffect, useState } from 'react'

/**
 * True once the element has come within `margin` of the viewport, and true from then on. Pass the
 * returned setter as the element's `ref`. Where IntersectionObserver does not exist it is true at
 * once, so the content still loads.
 */
export function useNearViewport<T extends Element>(margin = '600px'): readonly [(element: T | null) => void, boolean] {
  const [element, setElement] = useState<T | null>(null)
  const [near, setNear] = useState(() => typeof IntersectionObserver === 'undefined')

  useEffect(() => {
    if (near || !element) return undefined
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) setNear(true)
      },
      { rootMargin: margin },
    )
    observer.observe(element)
    return () => observer.disconnect()
  }, [element, near, margin])

  return [setElement, near] as const
}
