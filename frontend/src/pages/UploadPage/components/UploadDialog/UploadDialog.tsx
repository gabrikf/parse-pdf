import { X } from 'lucide-react'
import { useForm } from 'react-hook-form'

import type { ParserValue } from '../../../../shared/api/types'
import { Button } from '../../../../shared/components/Button'
import { Dialog } from '../../../../shared/components/Dialog'
import { DEFAULT_PARSER, PARSERS } from '../../../../shared/constants/parsers'
import { DropZone } from './components/DropZone'
import { FileRow } from './components/FileRow'
import { useUploadFlow } from './hooks/useUploadFlow'
import { FILE_STATE } from './types'
import styles from './UploadDialog.module.css'

interface FormValues {
  parser: ParserValue
}

/** Pick PDFs and a parser, send them in one request, and see each file's outcome (criteria 55-58). */
export function UploadDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const flow = useUploadFlow()
  const { register, handleSubmit, getValues } = useForm<FormValues>({ defaultValues: { parser: DEFAULT_PARSER } })

  const pending = flow.files.filter((item) => item.state === FILE_STATE.pending).length
  const sending = flow.files.some((item) => item.state === FILE_STATE.sending)
  const sent = flow.files.filter((item) => item.state === FILE_STATE.accepted || item.state === FILE_STATE.rejected).length
  const accepted = flow.files.filter((item) => item.state === FILE_STATE.accepted).length

  const uploadStep = pending > 0 || sent === 0
  const uploadLabel = pending === 1 ? 'Upload 1 file' : `Upload ${pending} files`
  const footerLabel = sending ? 'Uploading' : uploadLabel

  const close = () => {
    flow.reset()
    onClose()
  }

  return (
    <Dialog open={open} onClose={close} labelledBy="upload-title">
      <div style={{ display: 'contents' }}>
        <header className={styles.header}>
          <h2 id="upload-title" className={styles.title}>
            Upload PDFs
          </h2>
          <Button variant="icon" aria-label="Close" onClick={close}>
            <X size={22} aria-hidden="true" />
          </Button>
        </header>
        <div className={styles.body}>
          <DropZone onFiles={flow.add} limitMessage={flow.limitMessage} />
          <div className={styles.field}>
            <label htmlFor="upload-parser" className={styles.fieldLabel}>
              Parser
            </label>
            <select id="upload-parser" className={styles.select} {...register('parser')}>
              {PARSERS.map((parser) => (
                <option key={parser.value} value={parser.value}>
                  {parser.name} · {parser.output}
                </option>
              ))}
            </select>
          </div>
          {flow.files.length > 0 ? (
            <div className={styles.list}>
              <div className={styles.listTitle} role="status">
                {sent > 0 ? `${accepted} of ${flow.files.length} files uploaded` : `${flow.files.length} selected`}
              </div>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {flow.files.map((item) => (
                  <FileRow key={item.key} item={item} onRemove={flow.remove} onUnlock={(file, password) => void flow.unlock(file, getValues('parser'), password)} />
                ))}
              </ul>
            </div>
          ) : null}
          {flow.error ? (
            <p role="alert" className={styles.error}>
              {flow.error}
            </p>
          ) : null}
        </div>
        <footer className={styles.footer}>
          {uploadStep ? null : (
            <Button variant="secondary" onClick={flow.reset}>
              Add more files
            </Button>
          )}
          <Button
            variant="primary"
            disabled={uploadStep && pending === 0 && !sending}
            aria-busy={sending}
            onClick={uploadStep ? handleSubmit((values) => (sending ? undefined : flow.submit(values.parser))) : close}
          >
            {uploadStep ? footerLabel : 'Done'}
          </Button>
        </footer>
      </div>
    </Dialog>
  )
}
