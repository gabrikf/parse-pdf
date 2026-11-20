import { useState } from 'react'

import type { ParserValue } from '../../../../shared/api/types'
import { Button } from '../../../../shared/components/Button'
import { Dialog } from '../../../../shared/components/Dialog'
import { PARSERS } from '../../../../shared/constants/parsers'
import { ACTION } from '../DocumentFeed/types'
import styles from './ConfirmDialog.module.css'
import type { ConfirmRequest } from './types'
import { confirmCopy } from './utils'

interface ConfirmDialogProps {
  request: ConfirmRequest | null
  onCancel: () => void
  onConfirm: (request: ConfirmRequest) => void
}

function ParserChoice({ value, onChange }: { value: ParserValue; onChange: (parser: ParserValue) => void }) {
  return (
    <fieldset className={styles.fieldset}>
      <legend className={styles.legend}>Parser</legend>
      {PARSERS.map((parser) => (
        <label key={parser.value} className={styles.option}>
          <input
            type="radio"
            name="reparse-parser"
            value={parser.value}
            checked={value === parser.value}
            onChange={() => onChange(parser.value)}
          />
          <span>
            <span className={styles.name}>{parser.name}</span>
            <span className={styles.output}> · {parser.output}</span>
          </span>
        </label>
      ))}
    </fieldset>
  )
}

function ConfirmBody({ request, onCancel, onConfirm }: ConfirmDialogProps & { request: ConfirmRequest }) {
  const [parser, setParser] = useState<ParserValue>(request.parser ?? request.document.parser)
  const copy = confirmCopy(request)
  const reparse = request.action === ACTION.reparse

  return (
    <div className={styles.body}>
      <h2 id="confirm-title" className={styles.title}>
        {copy.title}
      </h2>
      <p id="confirm-text" className={styles.text}>
        {copy.body}
      </p>
      {reparse ? <ParserChoice value={parser} onChange={setParser} /> : null}
      <div className={styles.footer}>
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          variant={request.action === ACTION.remove ? 'danger' : 'primary'}
          onClick={() => onConfirm(reparse ? { ...request, parser } : request)}
        >
          {copy.confirm}
        </Button>
      </div>
    </div>
  )
}

/** Asks before a reparse, a retry or a permanent delete; Cancel sends nothing (criterion 62). */
export function ConfirmDialog({ request, onCancel, onConfirm }: ConfirmDialogProps) {
  return (
    <Dialog open={request !== null} onClose={onCancel} labelledBy="confirm-title" describedBy="confirm-text" role="alertdialog" width={440}>
      {request ? (
        <ConfirmBody
          key={`${request.action}-${request.document.id}`}
          request={request}
          onCancel={onCancel}
          onConfirm={onConfirm}
        />
      ) : null}
    </Dialog>
  )
}
