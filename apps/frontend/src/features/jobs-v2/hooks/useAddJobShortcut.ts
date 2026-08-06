'use client'

import { useEffect } from 'react'

const SHORTCUT_KEY = 'n'

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.tagName === 'INPUT'
    || target.tagName === 'TEXTAREA'
    || target.tagName === 'SELECT'
    || target.isContentEditable
}

export function useAddJobShortcut(onAddJob: () => void) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== SHORTCUT_KEY) return
      if (event.metaKey || event.ctrlKey || event.altKey) return
      if (isEditableTarget(event.target)) return
      event.preventDefault()
      onAddJob()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onAddJob])
}
