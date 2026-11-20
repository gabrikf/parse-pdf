import { act, cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useNearViewport } from './useNearViewport'

function Probe() {
  const [ref, near] = useNearViewport<HTMLDivElement>()
  return <div ref={ref}>{near ? 'near' : 'far'}</div>
}

type Callback = (entries: Pick<IntersectionObserverEntry, 'isIntersecting'>[]) => void

function installObserver() {
  const seen: { callback: Callback; options: IntersectionObserverInit | undefined; disconnect: () => void }[] = []
  class FakeObserver {
    disconnect = vi.fn()
    constructor(callback: Callback, options?: IntersectionObserverInit) {
      seen.push({ callback, options, disconnect: this.disconnect })
    }
    observe = vi.fn()
  }
  vi.stubGlobal('IntersectionObserver', FakeObserver)
  return seen
}

describe('useNearViewport', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('is far until the element nears the viewport, then near for good', () => {
    const seen = installObserver()
    render(<Probe />)
    expect(screen.getByText('far')).toBeTruthy()
    expect(seen[0]?.options?.rootMargin).toBe('600px')

    act(() => seen[0]?.callback([{ isIntersecting: false }]))
    expect(screen.getByText('far')).toBeTruthy()

    act(() => seen[0]?.callback([{ isIntersecting: true }]))
    expect(screen.getByText('near')).toBeTruthy()
    expect(seen[0]?.disconnect).toHaveBeenCalled()
  })

  it('is near at once where IntersectionObserver does not exist', () => {
    vi.stubGlobal('IntersectionObserver', undefined)
    render(<Probe />)
    expect(screen.getByText('near')).toBeTruthy()
  })
})
