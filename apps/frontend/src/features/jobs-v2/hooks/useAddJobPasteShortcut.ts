'use client'

import { useEffect } from 'react'
import { isUrlString } from '@/shared/lib/url-drag'

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.tagName === 'INPUT'
    || target.tagName === 'TEXTAREA'
    || target.tagName === 'SELECT'
    || target.isContentEditable
}

/**
 * Opens the Add Job drawer with the pasted URL when the user presses
 * Ctrl+V / Cmd+V on the Jobs page outside any editable element. The URL is
 * taken directly from the paste event's clipboardData, so no clipboard-read
 * permission is involved; non-URL content and pastes inside inputs keep the
 * native behavior.
 */
export function useAddJobPasteShortcut(onPasteUrl: (url: string) => void) {
  useEffect(() => {
    const handler = (event: ClipboardEvent) => {
      if (isEditableTarget(event.target)) return
      const text = event.clipboardData?.getData('text/plain')?.trim() ?? ''
      if (!isUrlString(text)) return
      event.preventDefault()
      onPasteUrl(text)
    }
    window.addEventListener('paste', handler)
    return () => window.removeEventListener('paste', handler)
  }, [onPasteUrl])
}
