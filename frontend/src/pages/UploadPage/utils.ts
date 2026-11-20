import type { Theme } from '../../shared/hooks/useTheme'

/** The theme control names the theme it switches to. */
export function themeLabel(theme: Theme): string {
  return theme === 'dark' ? 'Light mode' : 'Dark mode'
}
