'use client'

import { parseDateTime } from '@/shared/lib/parseDateTime'
import { formatTimeAgo } from '@/shared/lib/formatTimeAgo'
import { cn } from '@/shared/lib/utils'

export type DateTimeFormat = 'relative' | 'dateTime' | 'date' | 'time'

interface DateTimeProps {
  value: string | null | undefined
  format?: DateTimeFormat
  className?: string
  fallback?: string
}

/**
 * Renders an API timestamp in the browser's LOCAL timezone.
 *
 * Uses `parseDateTime` so timestamps the backend serializes without a timezone
 * marker (naive UTC) are read as UTC instead of being misinterpreted as local
 * time. Compact formats (`relative`, `date`, `time`) show the full local
 * datetime on hover via the `title` attribute.
 */
export default function DateTime({ value, format = 'dateTime', className, fallback = '—' }: DateTimeProps) {
  const date = parseDateTime(value)
  if (!date) {
    return <span className={className}>{fallback}</span>
  }

  const full = date.toLocaleString()

  let display: string
  switch (format) {
    case 'relative':
      display = formatTimeAgo(value as string)
      break
    case 'date':
      display = date.toLocaleDateString()
      break
    case 'time':
      display = date.toLocaleTimeString()
      break
    default:
      display = full
  }

  const showFullOnHover = format === 'relative' || format === 'date' || format === 'time'

  return (
    <span
      className={cn('whitespace-nowrap', className)}
      title={showFullOnHover ? full : undefined}
    >
      {display}
    </span>
  )
}
