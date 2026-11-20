import { CloudUpload } from 'lucide-react'
import { useEffect, useRef, useState, type DragEvent } from 'react'

import { Button } from '../../../../../shared/components/Button'
import { ACCEPT } from '../constants'
import styles from '../UploadDialog.module.css'

interface DropZoneProps {
  onFiles: (files: File[]) => void
  limitMessage: string | null
}

/** Files come in three ways: the picker, a drop, or a paste anywhere while the dialog is open. */
export function DropZone({ onFiles, limitMessage }: DropZoneProps) {
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    const paste = (event: ClipboardEvent) => {
      const files = [...(event.clipboardData?.files ?? [])]
      if (files.length > 0) {
        event.preventDefault()
        onFiles(files)
      }
    }
    window.addEventListener('paste', paste)
    return () => window.removeEventListener('paste', paste)
  }, [onFiles])

  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    onFiles([...event.dataTransfer.files])
  }

  return (
    <div
      className={`${styles.drop} ${dragging ? styles.dragging : ''}`}
      data-testid="drop-zone"
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={drop}
    >
      <span className={styles.dropIcon}>
        <CloudUpload size={28} strokeWidth={1.75} aria-hidden="true" />
      </span>
      <div className={styles.dropTitle}>Drop PDFs here, or paste them</div>
      <div className={styles.dropNote}>Up to 20 files, 50 MB each</div>
      {limitMessage ? (
        <div role="alert" className={styles.limit}>
          {limitMessage}
        </div>
      ) : null}
      <Button variant="raised" style={{ marginTop: 6 }} onClick={() => input.current?.click()}>
        Choose files
      </Button>
      <input
        ref={input}
        type="file"
        multiple
        accept={ACCEPT}
        aria-label="Choose PDF files"
        className="visually-hidden"
        tabIndex={-1}
        onChange={(event) => {
          onFiles([...(event.target.files ?? [])])
          event.target.value = ''
        }}
      />
    </div>
  )
}
