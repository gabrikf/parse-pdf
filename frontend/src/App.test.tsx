import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: false, media: query, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
    HTMLDialogElement.prototype.showModal ??= vi.fn()
    HTMLDialogElement.prototype.close ??= vi.fn()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('an unreachable api shows an error with a retry control', async () => {
    const fetchMock = vi.fn(async () => {
      throw new TypeError('Failed to fetch')
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    const alert = await screen.findByRole('alert', {}, { timeout: 5_000 })
    expect(alert).toHaveTextContent("Can't reach the server. Your files are safe; the feed will refresh when it's back.")
    const calls = fetchMock.mock.calls.length

    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await vi.waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThan(calls))
  })
})
