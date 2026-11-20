import type { RejectedFile, UploadResult } from '../../../../shared/api/types'
import { rejectionReason } from '../../../../shared/constants/messages'
import { FILE_STATE, type SelectedFile } from './types'

/**
 * Apply an upload answer to the files that were sent: a file named in `rejected` takes its code
 * and reason (first unmatched name wins, so two files with one name both resolve); the rest
 * were accepted.
 */
export function applyResult(sent: SelectedFile[], result: UploadResult): Map<string, SelectedFile> {
  const rejected = [...result.rejected]
  const out = new Map<string, SelectedFile>()
  for (const item of sent) {
    const index = rejected.findIndex((entry) => entry.filename === item.file.name)
    if (index === -1) {
      out.set(item.key, { ...item, state: FILE_STATE.accepted })
      continue
    }
    const [entry] = rejected.splice(index, 1) as [RejectedFile]
    out.set(item.key, { ...item, state: FILE_STATE.rejected, code: entry.code, reason: rejectionReason(entry.code, entry.message) })
  }
  return out
}

export function rejectedFromDetails(details: Record<string, unknown>): RejectedFile[] {
  const rejected = details.rejected
  return Array.isArray(rejected) ? (rejected as RejectedFile[]) : []
}

let counter = 0

export function toSelected(files: File[]): SelectedFile[] {
  return files.map((file) => {
    counter += 1
    return { key: `${counter}-${file.name}`, file, state: FILE_STATE.pending }
  })
}
