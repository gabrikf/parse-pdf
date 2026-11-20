import { House, Moon, SquarePlus, Sun } from 'lucide-react'

import type { Theme } from '../../../../shared/hooks/useTheme'
import { themeLabel } from '../../utils'
import styles from './TabBar.module.css'

interface TabBarProps {
  theme: Theme
  onToggleTheme: () => void
  onUpload: () => void
  onFeed: () => void
}

/** The bottom tab bar under 768 px: feed, upload, theme (criterion 70). */
export function TabBar({ theme, onToggleTheme, onUpload, onFeed }: TabBarProps) {
  return (
    <nav aria-label="Main" className={styles.bar}>
      <button type="button" aria-current="page" aria-label="Feed" className={styles.item} onClick={onFeed}>
        <House size={24} strokeWidth={2} aria-hidden="true" />
      </button>
      <button type="button" aria-label="Upload PDFs" className={styles.item} onClick={onUpload}>
        <SquarePlus size={24} strokeWidth={1.75} aria-hidden="true" />
      </button>
      <button type="button" aria-label={themeLabel(theme)} className={styles.item} onClick={onToggleTheme}>
        {theme === 'dark' ? <Sun size={24} strokeWidth={1.75} aria-hidden="true" /> : <Moon size={24} strokeWidth={1.75} aria-hidden="true" />}
      </button>
    </nav>
  )
}
