const IST_TIME_ZONE = 'Asia/Kolkata'
const TIME_ZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i

export function parseTimestamp(value) {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value !== 'string') return null

  let normalized = value.trim().replace(/^(\d{4}-\d{2}-\d{2})\s+/, '$1T')
  if (!normalized) return null
  normalized = normalized.replace(
    /\.(\d+)(?=(?:Z|[+-]\d{2}:?\d{2})?$)/i,
    (_, fraction) => `.${fraction.slice(0, 3).padEnd(3, '0')}`,
  )
  if (!TIME_ZONE_SUFFIX.test(normalized)) normalized += 'Z'

  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

export function timestampMillis(value) {
  return parseTimestamp(value)?.getTime() ?? null
}

export function formatIstDateTime(value) {
  const date = parseTimestamp(value)
  if (!date) return 'N/A'

  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: IST_TIME_ZONE,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).formatToParts(date)
  const formatted = Object.fromEntries(parts.map(({ type, value: part }) => [type, part]))
  return `${formatted.day} ${formatted.month} ${formatted.year}, ${formatted.hour}:${formatted.minute} ${formatted.dayPeriod.toUpperCase()} IST`
}

export function getWaitHours(value, now = Date.now()) {
  const timestamp = timestampMillis(value)
  if (timestamp === null || !Number.isFinite(now)) return 0
  return Math.max(0, Math.round((now - timestamp) / 3600000))
}

export function sortCasesByPriorityAndSubmission(items) {
  const priority = { HIGH: 0, MEDIUM: 1, LOW: 2 }
  return [...items].sort((a, b) => {
    const priorityDelta = (priority[String(a.urgency_level || 'LOW').toUpperCase()] ?? 99)
      - (priority[String(b.urgency_level || 'LOW').toUpperCase()] ?? 99)
    if (priorityDelta) return priorityDelta

    const aTime = timestampMillis(a.created_at)
    const bTime = timestampMillis(b.created_at)
    if (aTime === null) return bTime === null ? 0 : 1
    if (bTime === null) return -1
    return bTime - aTime
  })
}
