import { postJson, request } from './client'
import type { DocumentDto, FeedState, PageDto, ParserValue, UploadResult } from './types'

export const FEED_PAGE_SIZE = 20
export const ACTIVE_PAGE_SIZE = 50
export const PAGES_PAGE_SIZE = 50

export function listDocuments(state: FeedState, cursor: string | null, limit = FEED_PAGE_SIZE) {
  const query = new URLSearchParams({ state, limit: String(limit) })
  if (cursor) query.set('cursor', cursor)
  return request<DocumentDto[]>(`/documents?${query.toString()}`)
}

/** Every document in `state`, following `next_cursor` page by page until it is null. */
export async function listAllDocuments(state: FeedState, limit: number) {
  const documents: DocumentDto[] = []
  let cursor: string | null = null
  do {
    const page = await listDocuments(state, cursor, limit)
    documents.push(...page.data)
    cursor = page.meta.next_cursor ?? null
  } while (cursor)
  return documents
}

export function getPages(id: string, offset: number, limit = PAGES_PAGE_SIZE) {
  const query = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return request<PageDto[]>(`/documents/${encodeURIComponent(id)}/pages?${query.toString()}`)
}

export function uploadDocuments(files: File[], parser: ParserValue, password?: string) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file, file.name))
  form.append('parser', parser)
  if (password) form.append('password', password)
  return request<UploadResult>('/documents', { method: 'POST', body: form })
}

export function reparseDocument(id: string, parser: ParserValue) {
  return postJson<DocumentDto>(`/documents/${encodeURIComponent(id)}/reparse`, { parser })
}

export function requeueDocument(id: string) {
  return request<DocumentDto>(`/documents/${encodeURIComponent(id)}/requeue`, { method: 'POST' })
}

export function deleteDocument(id: string) {
  return request<{ id: string; deleted: boolean }>(`/documents/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
