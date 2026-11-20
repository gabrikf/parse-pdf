import { FileText, House, Moon, SquarePlus, Sun } from 'lucide-react'

import type { Theme } from '../../../../shared/hooks/useTheme'
import { themeLabel } from '../../utils'
import styles from './SideRail.module.css'

interface SideRailProps {
  theme: Theme
  onToggleTheme: () => void
  onUpload: () => void
  onFeed: () => void
}

/** The left rail from 768 px: icons only, with labels and the wordmark from 1280 px. */
export function SideRail({ theme, onToggleTheme, onUpload, onFeed }: SideRailProps) {
  const label = themeLabel(theme)
  return (
    <nav aria-label="Main" className={styles.rail}>
      <div className={styles.wordmark}>
        Parse <span>PDF</span>
      </div>
      <div className={styles.logo}>
        <FileText size={28} strokeWidth={1.75} role="img" aria-label="Parse PDF" />
      </div>
      <div className={styles.items}>
        <button type="button" aria-current="page" aria-label="Feed" className={`${styles.item} ${styles.current}`} onClick={onFeed}>
          <House size={24} strokeWidth={2} aria-hidden="true" />
          <span className={styles.label}>Feed</span>
        </button>
        <button type="button" aria-label="Upload PDFs" className={styles.item} onClick={onUpload}>
          <SquarePlus size={24} strokeWidth={1.75} aria-hidden="true" />
          <span className={styles.label}>Upload</span>
        </button>
        <button type="button" aria-label={label} className={styles.item} onClick={onToggleTheme}>
          {theme === 'dark' ? <Sun size={24} strokeWidth={1.75} aria-hidden="true" /> : <Moon size={24} strokeWidth={1.75} aria-hidden="true" />}
          <span className={styles.label}>{label}</span>
        </button>
      </div>
    </nav>
  )
}
