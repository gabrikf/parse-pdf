const MB = 1024 * 1024

/** `2.3 MB`, the unit file pickers show (50 MB = 52,428,800 bytes). */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < MB) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / MB).toFixed(1)} MB`
}

export function formatCount(value: number): string {
  return value.toLocaleString('en-US')
}

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${formatCount(count)} ${count === 1 ? one : many}`
}

/** `just now`, `3 min ago`, `1 h ago`, `2 d ago`. */
export function timeAgo(iso: string, now: number = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000))
  if (seconds < 45) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  return `${Math.round(hours / 24)} d ago`
}

/** `lecture-notes-week-3.pdf` -> `lecture-notes-week-3`, for the stories row. */
export function shortName(filename: string): string {
  return filename.replace(/\.pdf$/i, '')
}
