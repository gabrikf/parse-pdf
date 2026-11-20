import { request } from './client'
import type { BudgetDto, SessionDto } from './types'

/** Create a session, or reuse the one the `pp_session` cookie holds (criterion 54). */
export function openSession() {
  return request<SessionDto>('/sessions', { method: 'POST' })
}

export function getBudget() {
  return request<BudgetDto>('/budget')
}
