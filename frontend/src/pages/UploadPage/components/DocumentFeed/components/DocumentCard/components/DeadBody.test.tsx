import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { makeDocument } from '../../../../../../../test/documents'
import { DeadBody } from './DeadBody'

const handlers = { onOpenPages: () => undefined, onAsk: () => undefined }

describe('DeadBody', () => {
  afterEach(cleanup)

  it("shows the API's hint, which names the tries and the last cause", () => {
    const hint = 'Processing stopped after 5 tries. The last error was: the model provider timed out.'
    render(<DeadBody document={makeDocument({ status: 'dead', error_code: 'max_deliveries', hint })} handlers={handlers} />)
    expect(screen.getByText(hint)).toBeVisible()
  })

  it('falls back to the copy for its error code when there is no hint', () => {
    render(<DeadBody document={makeDocument({ status: 'dead', error_code: 'max_deliveries' })} handlers={handlers} />)
    expect(screen.getByText('Processing stopped after repeated failures.')).toBeVisible()
  })
})
