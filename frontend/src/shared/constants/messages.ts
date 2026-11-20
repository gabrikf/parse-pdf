import { ApiError } from '../api/errors'

/** What the page says for each error code the API returns (criterion 57). */

export const REJECTION_REASON: Record<string, string> = {
  not_pdf: "This file isn't a PDF. Export it as a PDF and add it again.",
  empty: 'This file is empty. Pick the PDF again.',
  unreadable_pdf: "This PDF can't be opened. It may be damaged.",
  password_required: 'This PDF needs a password. It is used once to unlock the file and never stored.',
  wrong_password: "That password didn't unlock this PDF. Try again.",
  model_budget_exhausted: "Today's model pages are used up. Use PyPDF, or try again after 00:00 UTC.",
}

export const DEAD_REASON: Record<string, string> = {
  // The API's hint names the real number of tries and the last cause; this is only its fallback.
  max_deliveries: 'Processing stopped after repeated failures.',
  guardrail_rejected: 'The safety check flagged this document, so no summary was written.',
  provider_rejected: 'The model provider refused this file.',
  provider_out_of_credits: 'The shared model key is out of credit. Try PyPDF, or come back later.',
  provider_not_configured: 'No model key is set on this server. Use PyPDF instead.',
  model_output_invalid: "The model's pages didn't match the PDF after 3 tries.",
  parse_timeout: "This PDF took too long to read, so parsing stopped.",
  unreadable_pdf: "This PDF couldn't be read.",
}

/**
 * The `no_text` card's hint, in the page's words: the API's `hint` names the parser by its id
 * for API clients, and the page names it as the parser select does (AD-039).
 */
export const NO_TEXT_HINT = 'This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.'

export const PASSWORD_CODES = new Set(['password_required', 'wrong_password'])

const CHANGED_SINCE = 'This document changed since you opened this, so nothing was sent. The feed now shows where it is.'
const GONE = 'This document is gone. It may have been deleted in another tab.'

/** Why a reparse, retry or delete was refused, shown inside its confirmation. */
export const ACTION_ERROR: Record<string, string> = {
  document_busy: 'This document is being processed right now. Try again when it finishes.',
  not_reparsable: CHANGED_SINCE,
  not_dead: CHANGED_SINCE,
  document_not_found: GONE,
  not_found: GONE,
  model_budget_exhausted: REJECTION_REASON.model_budget_exhausted ?? '',
}

export function actionError(error: unknown): string {
  if (error instanceof ApiError) return ACTION_ERROR[error.code] ?? error.message
  return 'Something went wrong. Try again.'
}

export function rejectionReason(code: string, fallback: string): string {
  return REJECTION_REASON[code] ?? fallback
}

export function deadReason(code: string | null): string {
  return (code && DEAD_REASON[code]) || 'Processing failed.'
}
