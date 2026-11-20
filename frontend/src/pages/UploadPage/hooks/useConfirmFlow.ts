import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { deleteDocument, reparseDocument, requeueDocument } from '../../../shared/api/documents'
import { UnreachableError } from '../../../shared/api/errors'
import { queryKeys } from '../../../shared/api/queryKeys'
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
 */
export function useConfirmFlow() {
  const client = useQueryClient()
  const { report } = useNotice()
  const [asking, setAsking] = useState<ConfirmRequest | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    await client.invalidateQueries({ queryKey: queryKeys.documents })
    await client.invalidateQueries({ queryKey: queryKeys.budget })
  }

  const mutation = useMutation({
    mutationFn: send,
    onSuccess: async () => {
      setAsking(null)
      await refresh()
    },
    onError: async (failure) => {
      if (failure instanceof UnreachableError) {
        setAsking(null)
        report(failure)
        return
      }
      setError(actionError(failure))
      await refresh()
    },
  })

  const ask = (request: ConfirmRequest) => {
    setError(null)
    setAsking(request)
  }
  const cancel = () => {
    setError(null)
    setAsking(null)
  }
  const confirm = (request: ConfirmRequest) => {
    if (mutation.isPending) return
    setError(null)
    mutation.mutate(request)
  }

  return { asking, error, pending: mutation.isPending, ask, cancel, confirm }
}
