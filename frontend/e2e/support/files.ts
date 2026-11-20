import { readFileSync } from 'node:fs'
import path from 'node:path'

import { makePdf, textPdf } from './pdf'

export interface FilePayload {
  name: string
  mimeType: string
  buffer: Buffer
}

const SAMPLES = path.resolve(import.meta.dirname, '../../../samples')

export const SAMPLE = {
  dummy: 'w3c-dummy.pdf',
  constitution: 'constitution-of-the-united-states.pdf',
  scanned: 'constitution-scanned-p1-3.pdf',
  locked: 'w3c-dummy-locked.pdf',
} as const

/** The demo password of `samples/w3c-dummy-locked.pdf`, read from `samples/SOURCES.md`. */
export function lockedSamplePassword(): string {
  const sources = readFileSync(path.join(SAMPLES, 'SOURCES.md'), 'utf8')
  const found = /Demo password: `([^`]+)`/.exec(sources)?.[1]
  if (!found) throw new Error('samples/SOURCES.md names no demo password')
  return found
}

export function pdfFile(name: string, buffer: Buffer): FilePayload {
  return { name, mimeType: 'application/pdf', buffer }
}

export function sample(name: string): FilePayload {
  return pdfFile(name, readFileSync(path.join(SAMPLES, name)))
}

/** A text PDF of `count` pages. */
export function pagesFile(name: string, count: number): FilePayload {
  return pdfFile(name, textPdf(count))
}

/** 1,001 blank pages: stored as `too_large` without being parsed. */
export function tooLargeFile(name: string): FilePayload {
  return pdfFile(name, makePdf(Array.from({ length: 1001 }, () => '')))
}

/** Text whose first model call the stub refuses once, so the document ends `dead`; a retry passes. */
export function failOnceFile(name: string): FilePayload {
  const token = `STUB-FAIL-ONCE-${crypto.randomUUID()}`
  return pdfFile(name, makePdf([`${token} A short page that the stub refuses once.`]))
}
