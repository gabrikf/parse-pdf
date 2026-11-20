import { PARSER, type ParserValue } from '../api/types'

export interface ParserInfo {
  value: ParserValue
  name: string
  output: string
  guide: string
}

/** The three parsers, in the order the select and the guide show them (criterion 55). */
export const PARSERS: readonly ParserInfo[] = [
  { value: PARSER.pypdf, name: 'PyPDF', output: 'plain text', guide: 'Plain text from PDFs that already have a text layer. Fast, no model.' },
  { value: PARSER.gemini, name: 'Gemini 3.1 Flash Lite', output: 'markdown', guide: 'Markdown with headings, lists and tables. Reads scanned pages.' },
  { value: PARSER.gpt, name: 'GPT-5 Mini', output: 'OCR', guide: 'OCR for scans and photographed pages, returned as markdown.' },
]

export const DEFAULT_PARSER: ParserValue = PARSER.pypdf

export const SUMMARY_MODEL_NAME = 'Gemini 3.1 Flash Lite'

export function parserName(value: ParserValue): string {
  return PARSERS.find((parser) => parser.value === value)?.name ?? value
}
