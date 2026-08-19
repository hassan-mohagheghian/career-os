import { parseDateTime } from './parseDateTime'

/**
 * Convert an API timestamp into the value expected by a `datetime-local`
 * input (local wall-clock time, `YYYY-MM-DDTHH:mm`). Returns '' for invalid
 * or empty input.
 */
export function toDatetimeLocalInput(value: string | null | undefined): string {
  const date = parseDateTime(value)
  if (!date) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/**
 * Convert a `datetime-local` input value (naive local wall-clock time) into an
 * ISO string carrying the browser's UTC offset, so the backend stores the same
 * real instant the user picked. Returns null for empty/invalid input.
 */
export function toIsoFromLocalInput(value: string): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  const pad = (n: number) => String(n).padStart(2, '0')
  const offset = -date.getTimezoneOffset()
  const sign = offset >= 0 ? '+' : '-'
  const abs = Math.abs(offset)
  const iso = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:00${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
  return iso
}