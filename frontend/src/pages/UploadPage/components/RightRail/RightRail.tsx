import type { BudgetDto } from '../../../../shared/api/types'
import { PARSERS, SUMMARY_MODEL_NAME } from '../../../../shared/constants/parsers'
import { formatCount } from '../../../../shared/utils/format'
import { PRIVACY_NOTE } from '../../constants'
import styles from './RightRail.module.css'

/** From 1024 px: the parser guide and today's model page budget (criterion 70). */
export function RightRail({ budget }: { budget: BudgetDto | undefined }) {
  const percent = budget ? Math.min(100, Math.round((budget.used / Math.max(1, budget.limit)) * 100)) : 0
  return (
    <aside aria-label="About parsing" className={styles.rail}>
      <section className={styles.section}>
        <h2 className={styles.heading}>Parsers</h2>
        {PARSERS.map((parser) => (
          <div key={parser.value} className={styles.parser}>
            <div className={styles.name}>{parser.name}</div>
            <div className={styles.guide}>{parser.guide}</div>
          </div>
        ))}
        <div className={styles.note}>Every summary is written by {SUMMARY_MODEL_NAME}.</div>
      </section>
      <section className={styles.budget} aria-label="Model pages today">
        <h2 className={styles.heading}>Model pages today</h2>
        {budget ? (
          <>
            <div className={styles.figure}>
              <span className={styles.used}>{formatCount(budget.used)}</span>{' '}
              <span className={styles.limit}>of {formatCount(budget.limit)}</span>
            </div>
            <div role="img" aria-label={`${percent} percent of today's model pages used`} className={styles.meter}>
              <div className={styles.fill} style={{ width: `${percent}%` }} />
            </div>
          </>
        ) : null}
        <div className={styles.note}>Resets at 00:00 UTC. PyPDF parsing doesn&apos;t count.</div>
      </section>
      <p className={styles.privacy}>{PRIVACY_NOTE}</p>
    </aside>
  )
}
