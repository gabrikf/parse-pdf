/** DTOs mirroring the backend envelope `{data, error, meta}` (door 3). */

export const STATUS = {
  queued: 'queued',
  processing: 'processing',
  ready: 'ready',
  noText: 'no_text',
  dead: 'dead',
  tooLarge: 'too_large',
} as const

export type DocumentStatus = (typeof STATUS)[keyof typeof STATUS]

export const PARSER = {
  pypdf: 'pypdf',
  gemini: 'gemini-3.1-flash-lite',
  gpt: 'gpt-5-mini',
} as const

export type ParserValue = (typeof PARSER)[keyof typeof PARSER]

export const FEED_STATE = { parsed: 'parsed', failed: 'failed', active: 'active', all: 'all' } as const

export type FeedState = (typeof FEED_STATE)[keyof typeof FEED_STATE]

export interface DocumentDto {
  id: string
  filename: string
  parser: ParserValue
  status: DocumentStatus
  error_code: string | null
  hint: string | null
  page_count: number
  size_bytes: number
  created_at: string
  updated_at: string
  summary: string | null
}

export interface RejectedFile {
  filename: string
  code: string
  message: string
}

export interface UploadResult {
  documents: DocumentDto[]
  rejected: RejectedFile[]
}

export interface PageDto {
  number: number
  content: string
  format: 'text' | 'markdown'
}

export interface BudgetDto {
  used: number
  limit: number
  resets_at: string
}

export interface SessionDto {
  session_id: string
  expires_at: string
}

export type FeedCounts = Record<FeedState, number>

export interface Meta {
  request_id?: string
  next_cursor?: string | null
  total?: number
  counts?: FeedCounts
}

export interface Envelope<T> {
  data: T
  error: { code: string; message: string; details?: Record<string, unknown> } | null
  meta: Meta
}
