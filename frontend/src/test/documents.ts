import type { DocumentDto } from '../shared/api/types'

/** A document as the API returns it, with overrides. */
export function makeDocument(overrides: Partial<DocumentDto> = {}): DocumentDto {
  return {
    id: 'doc-1',
    filename: 'report.pdf',
    parser: 'pypdf',
    status: 'queued',
    error_code: null,
    hint: null,
    page_count: 3,
    size_bytes: 13_264,
    created_at: '2026-11-20T00:00:00Z',
    updated_at: '2026-11-20T00:00:00Z',
    summary: null,
    ...overrides,
  }
}
