import { useMutation, useQueryClient } from '@tanstack/react-query'

import { deleteDocument, reparseDocument, requeueDocument } from '../../../shared/api/documents'
import { queryKeys } from '../../../shared/api/queryKeys'
import type { ParserValue } from '../../../shared/api/types'
import { useNotice } from '../context/notice'

/** Reparse, retry (requeue) and delete; each refreshes the lists it changes. */
export function useDocumentActions() {
  const client = useQueryClient()
  const { report } = useNotice()

  const refresh = async () => {
    await client.invalidateQueries({ queryKey: queryKeys.documents })
    await client.invalidateQueries({ queryKey: queryKeys.budget })
  }

  const reparse = useMutation({
    mutationFn: ({ id, parser }: { id: string; parser: ParserValue }) => reparseDocument(id, parser),
    onSuccess: refresh,
    onError: report,
  })
  const requeue = useMutation({ mutationFn: (id: string) => requeueDocument(id), onSuccess: refresh, onError: report })
  const remove = useMutation({ mutationFn: (id: string) => deleteDocument(id), onSuccess: refresh, onError: report })

  return { reparse, requeue, remove }
}
