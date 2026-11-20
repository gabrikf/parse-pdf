import { Check, LoaderCircle, LockKeyhole, TriangleAlert, X } from 'lucide-react'
import { useId, useState } from 'react'

import { Button } from '../../../../../shared/components/Button'
import { PASSWORD_CODES } from '../../../../../shared/constants/messages'
import { formatBytes } from '../../../../../shared/utils/format'
import { FILE_STATE, type SelectedFile } from '../types'
import styles from '../UploadDialog.module.css'

interface FileRowProps {
  item: SelectedFile
  onRemove: (key: string) => void
  onUnlock: (item: SelectedFile, password: string) => void
}

function StateIcon({ item }: { item: SelectedFile }) {
  if (item.state === FILE_STATE.accepted) return <Check size={20} color="var(--ok)" aria-label="Uploaded" />
  if (item.state === FILE_STATE.sending) return <LoaderCircle size={20} color="var(--muted)" aria-label="Sending" />
  if (item.code && PASSWORD_CODES.has(item.code)) return <LockKeyhole size={20} color="var(--warn)" aria-label="Locked" />
  if (item.state === FILE_STATE.rejected) return <TriangleAlert size={20} color="var(--danger)" aria-label="Refused" />
  return null
}

/** One file: name and size, then its outcome; a locked file gets a password field (criterion 58). */
export function FileRow({ item, onRemove, onUnlock }: FileRowProps) {
  const fieldId = useId()
  const [password, setPassword] = useState('')
  const locked = item.state === FILE_STATE.rejected && item.code !== undefined && PASSWORD_CODES.has(item.code)

  return (
    <li className={styles.row} data-file={item.file.name} data-state={item.state}>
      <div className={styles.rowLine}>
        <StateIcon item={item} />
        <span className={styles.rowName}>{item.file.name}</span>
        <span className={styles.size}>{formatBytes(item.file.size)}</span>
        {item.state === FILE_STATE.pending ? (
          <Button variant="icon" aria-label={`Remove ${item.file.name}`} onClick={() => onRemove(item.key)}>
            <X size={18} aria-hidden="true" />
          </Button>
        ) : null}
      </div>
      {item.state === FILE_STATE.rejected && !locked ? (
        <div className={styles.reason} style={{ color: 'var(--danger)' }}>
          {item.reason}
        </div>
      ) : null}
      {locked ? (
        <form
          className={styles.unlock}
          onSubmit={(event) => {
            event.preventDefault()
            if (password) onUnlock(item, password)
          }}
        >
          <label htmlFor={fieldId} style={{ fontSize: 13, color: 'var(--warn)', fontWeight: 500 }}>
            {item.reason}
          </label>
          <div className={styles.unlockRow}>
            <input
              id={fieldId}
              className={styles.input}
              type="password"
              autoComplete="off"
              placeholder="Password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Button type="submit" variant="primary">
              Unlock
            </Button>
          </div>
        </form>
      ) : null}
    </li>
  )
}
