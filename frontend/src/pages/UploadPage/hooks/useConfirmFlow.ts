import { useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'

import { deleteDocument, reparseDocument, requeueDocument } from '../../../shared/api/documents'
import { UnreachableError } from '../../../shared/api/errors'
import { refreshDocuments } from '../../../shared/api/refreshDocuments'
import { actionError } from '../../../shared/constants/messages'
import type { ConfirmRequest } from '../components/ConfirmDialog'
import { ACTION } from '../components/DocumentFeed/types'
import { useNotice } from '../context/notice'

function send({ action, document, parser }: ConfirmRequest): Promise<unknown> {
  if (action === ACTION.reparse) return reparseDocument(document.id, parser ?? document.parser)
  if (action === ACTION.requeue) return requeueDocument(document.id)
  return deleteDocument(document.id)
}

/**
 * Ask, then reparse, retry or delete (criterion 62). Success closes the confirmation; a refusal
 * (busy, changed, gone, out of budget) keeps it open with the reason, and either way the lists
 * refetch. An unreachable API closes it and shows the page's offline banner.
 *
 * Each answer belongs to the confirmation that sent it: if that one was cancelled and another
 * opened meanwhile, the answer only refreshes the lists and never closes or labels the new one.
 */
export function useConfirmFlow() {
  const client = useQueryClient()
  const { report } = useNotice()
  const [asking, setAsking] = useState<ConfirmRequest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pendingFor, setPendingFor] = useState<ConfirmRequest | null>(null)
  const open = useRef<ConfirmRequest | null>(null)
  // Read in the click handler: a second click before the next render still sees the first.
  const sending = useRef<ConfirmRequest | null>(null)

  const show = (request: ConfirmRequest | null) => {
    open.current = request
    setError(null)
    setAsking(request)
  }

  const refresh = () => refreshDocuments(client)

  const confirm = async (request: ConfirmRequest) => {
    const owner = open.current
    if (owner === null || sending.current === owner) return
    sending.current = owner
    setError(null)
    setPendingFor(owner)
    try {
      await send(request)
      if (open.current === owner) show(null)
    } catch (failure) {
      if (failure instanceof UnreachableError) {
        if (open.current === owner) show(null)
        report(failure)
      } else if (open.current === owner) {
        setError(actionError(failure))
      }
    } finally {
      if (sending.current === owner) sending.current = null
      setPendingFor((current) => (current === owner ? null : current))
    }
    await refresh()
  }

  return {
    asking,
    error,
    pending: asking !== null && pendingFor === asking,
    ask: (request: ConfirmRequest) => show(request),
    cancel: () => show(null),
    confirm: (request: ConfirmRequest) => void confirm(request),
  }
}
