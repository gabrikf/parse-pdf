export const FILE_STATE = { pending: 'pending', sending: 'sending', accepted: 'accepted', rejected: 'rejected' } as const

export type FileState = (typeof FILE_STATE)[keyof typeof FILE_STATE]

/** One file in the dialog, before and after it is sent. */
export interface SelectedFile {
  key: string
  file: File
  state: FileState
  code?: string
  reason?: string
}
