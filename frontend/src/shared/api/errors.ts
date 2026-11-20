/** Errors the page tells apart: the API said no, or the API could not be reached. */

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly retryAfterSeconds: number | null
  readonly details: Record<string, unknown>

  constructor(status: number, code: string, message: string, retryAfter: number | null, details: Record<string, unknown> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.retryAfterSeconds = retryAfter
    this.details = details
  }
}

export class UnreachableError extends Error {
  constructor() {
    super("Can't reach the server")
    this.name = 'UnreachableError'
  }
}

export function isRateLimited(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 429
}
