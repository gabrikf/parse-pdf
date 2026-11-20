import ReactMarkdown from 'react-markdown'

import { rawHtmlAsText } from './rawHtmlAsText'

interface MarkdownProps {
  source: string
  className: string | undefined
}

/** Markdown with no raw HTML: tags show as text, links stay inert text-safe anchors. */
export function Markdown({ source, className }: MarkdownProps) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[rawHtmlAsText]}>{source}</ReactMarkdown>
    </div>
  )
}
