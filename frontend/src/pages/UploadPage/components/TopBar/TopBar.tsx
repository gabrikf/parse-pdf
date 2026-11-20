import type { BudgetDto } from '../../../../shared/api/types'
import { formatCount } from '../../../../shared/utils/format'
import styles from './TopBar.module.css'

/** The phone header: wordmark and today's model page budget. */
export function TopBar({ budget }: { budget: BudgetDto | undefined }) {
  return (
    <header className={styles.bar}>
      <div className={styles.wordmark}>
        Parse <span>PDF</span>
      </div>
      {budget ? (
        <div className={styles.budget}>
          {formatCount(budget.used)} of {formatCount(budget.limit)}
          <br />
          model pages today
        </div>
      ) : null}
    </header>
  )
}
