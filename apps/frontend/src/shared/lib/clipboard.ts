'use client'

const URL_RE = /^https?:\/\/\S+$/i

export async function readClipboardUrl(): Promise<string | null> {
  if (typeof window === 'undefined' || !navigator.clipboard?.readText) return null
  try {
    const text = (await navigator.clipboard.readText())?.trim() ?? ''
    return URL_RE.test(text) ? text : null
  } catch {
    return null
  }
}
