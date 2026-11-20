import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useRef, useState } from 'react'

import { uploadDocuments } from '../../../../../shared/api/documents'
import { ApiError } from '../../../../../shared/api/errors'
import { refreshDocuments } from '../../../../../shared/api/refreshDocuments'
import type { ParserValue, UploadResult } from '../../../../../shared/api/types'
import { MAX_FILES } from '../../../../../shared/constants/limits'
import { useNotice } from '../../../context/notice'
import { TOO_MANY_FILES } from '../constants'
import { FILE_STATE, type SelectedFile } from '../types'
import { applyResult, rejectedFromDetails, toSelected } from '../utils'

/**
 * The dialog's files: add (capped at 20, criterion 56), send once (criterion 57), and re-send a
 * locked file alone with its password (criterion 58).
 */
export function useUploadFlow() {
  const client = useQueryClient()
  const { report } = useNotice()
  const [files, setFiles] = useState<SelectedFile[]>([])
  const [limitMessage, setLimitMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Bumped by `reset`: an answer for a batch sent before the dialog was closed changes nothing.
  const generation = useRef(0)

  const add = useCallback(
    (incoming: File[]) => {
      const room = Math.max(0, MAX_FILES - files.filter((item) => item.state === FILE_STATE.pending).length)
      setLimitMessage(incoming.length > room ? TOO_MANY_FILES : null)
      const added = toSelected(incoming.slice(0, room))
      setFiles((current) => [...current, ...added])
    },
    [files],
  )

  const remove = useCallback((key: string) => {
    setFiles((current) => current.filter((item) => item.key !== key))
    setLimitMessage(null)
  }, [])

  const send = useCallback(
    async (batch: SelectedFile[], parser: ParserValue, password?: string) => {
      const keys = new Set(batch.map((item) => item.key))
      const sent = generation.current
      setError(null)
      setFiles((current) => current.map((item) => (keys.has(item.key) ? { ...item, state: FILE_STATE.sending } : item)))
      let result: UploadResult
      try {
        result = (await uploadDocuments(batch.map((item) => item.file), parser, password)).data
      } catch (caught) {
        if (caught instanceof ApiError && caught.code === 'all_files_rejected') {
          result = { documents: [], rejected: rejectedFromDetails(caught.details) }
        } else {
          report(caught)
          if (sent !== generation.current) return
          setError(caught instanceof Error ? caught.message : 'The upload failed.')
          setFiles((current) => current.map((item) => (keys.has(item.key) ? { ...item, state: FILE_STATE.pending } : item)))
          return
        }
      }
      if (sent !== generation.current) {
        await refreshDocuments(client)
        return
      }
      const updated = applyResult(batch, result)
      setFiles((current) => current.map((item) => updated.get(item.key) ?? item))
      await refreshDocuments(client)
    },
    [client, report],
  )

  const submit = useCallback(
    (parser: ParserValue) => send(files.filter((item) => item.state === FILE_STATE.pending), parser),
    [files, send],
  )

  const unlock = useCallback((item: SelectedFile, parser: ParserValue, password: string) => send([item], parser, password), [send])

  const reset = useCallback(() => {
    generation.current += 1
    setFiles([])
    setLimitMessage(null)
    setError(null)
  }, [])

  return { files, add, remove, submit, unlock, reset, limitMessage, error }
}
