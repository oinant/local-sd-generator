/**
 * Formatting utilities for dates and session names.
 */

/**
 * Format session name from folder format to display format.
 *
 * Supports two formats:
 * - Old: 2025-10-14_163854_hassaku_actualportrait.prompt
 * - New: 20251014_163854-Hassaku-fantasy-default
 *
 * @param {string} sessionName - Raw session folder name
 * @returns {string} Formatted display name (e.g., "2025-10-14 · hassaku actualportrait")
 */
export function formatSessionName(sessionName) {
  // Try old format (YYYY-MM-DD_HHMMSS_name)
  const oldMatch = sessionName.match(/^(\d{4}-\d{2}-\d{2})_\d{6}_(.+)/)
  if (oldMatch) {
    const date = oldMatch[1]
    const name = oldMatch[2].replace('.prompt', '')
    return `${date} · ${name}`
  }

  // Try new format (YYYYMMDD_HHMMSS-name)
  const newMatch = sessionName.match(/^(\d{4})(\d{2})(\d{2})_\d{6}-(.+)/)
  if (newMatch) {
    const date = `${newMatch[1]}-${newMatch[2]}-${newMatch[3]}`
    const name = newMatch[4].replace(/-/g, ' ')
    return `${date} · ${name}`
  }

  // Fallback: return as-is
  return sessionName
}

/**
 * Format date to French locale.
 *
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date (e.g., "7 nov. 2025, 14:30")
 */
export function formatDate(date) {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

/**
 * Format date to short French locale (without time).
 *
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date (e.g., "7 nov. 2025")
 */
export function formatDateShort(date) {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }).format(date)
}
