'use client'

const URL_RE = /^https?:\/\/\S+$/i

export function isUrlString(text: string | null | undefined): text is string {
  return !!text && URL_RE.test(text.trim())
}

function firstUrl(lines: string[]): string | null {
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    if (isUrlString(trimmed)) return trimmed
  }
  return null
}

/**
 * Extract the first http(s) URL from a drag-and-drop DataTransfer.
 *
 * When dragging a link from another browser tab the URL is delivered via the
 * `text/uri-list` type (possibly multiple newline-separated URLs with `#`
 * comment lines). Falls back to `text/plain`. Returns null when nothing looks
 * like a URL.
 */
export function extractUrlFromDataTransfer(
  dataTransfer: Pick<DataTransfer, 'getData'> | null | undefined
): string | null {
  if (!dataTransfer) return null

  const uriList = dataTransfer.getData('text/uri-list')?.trim()
  if (uriList) {
    const fromList = firstUrl(uriList.split(/\r?\n/))
    if (fromList) return fromList
  }

  const plain = dataTransfer.getData('text/plain')?.trim()
  if (isUrlString(plain)) return plain

  return null
}

/** True when the DataTransfer carries a URL-ish payload we can drop. */
export function dataTransferHasUrl(dataTransfer: DataTransfer | null | undefined): boolean {
  if (!dataTransfer) return false
  const types = Array.from(dataTransfer.types ?? [])
  return types.includes('text/uri-list') || types.includes('text/plain')
}