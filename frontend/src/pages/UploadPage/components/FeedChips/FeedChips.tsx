import { FEED_STATE, type FeedCounts, type FeedState } from '../../../../shared/api/types'
import styles from './FeedChips.module.css'

export type ChipValue = Exclude<FeedState, 'active'>

const CHIPS: readonly { value: ChipValue; label: string }[] = [
  { value: FEED_STATE.parsed, label: 'Parsed' },
  { value: FEED_STATE.failed, label: 'Failed' },
  { value: FEED_STATE.all, label: 'All' },
]

interface FeedChipsProps {
  value: ChipValue
  counts: FeedCounts | undefined
  onChange: (value: ChipValue) => void
}

/** Parsed (default), Failed and All, each with its count; they filter the feed only (criterion 72). */
export function FeedChips({ value, counts, onChange }: FeedChipsProps) {
  return (
    <div role="group" aria-label="Show in feed" className={styles.chips}>
      {CHIPS.map((chip) => (
        <button
          key={chip.value}
          type="button"
          aria-pressed={chip.value === value}
          className={styles.chip}
          onClick={() => onChange(chip.value)}
        >
          {chip.label} <span className={styles.count}>{counts?.[chip.value] ?? 0}</span>
        </button>
      ))}
    </div>
  )
}
