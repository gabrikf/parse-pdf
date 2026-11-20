import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Markdown } from './Markdown'

describe('Markdown', () => {
  it('markdown shows raw html as literal text', () => {
    const { container } = render(<Markdown source={'## Notes\n\n<script>alert(1)</script>\n\nText <b>bold</b>'} className={undefined} />)

    expect(screen.getByRole('heading', { name: 'Notes' })).toBeInTheDocument()
    expect(container.querySelector('script')).toBeNull()
    expect(container.querySelector('b')).toBeNull()
    expect(container).toHaveTextContent('<script>alert(1)</script>')
    expect(container).toHaveTextContent('Text <b>bold</b>')
  })
})
