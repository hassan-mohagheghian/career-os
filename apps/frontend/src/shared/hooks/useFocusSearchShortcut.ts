'use client'

import { useEffect, type RefObject } from 'react'

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.tagName === 'INPUT'
    || target.tagName === 'TEXTAREA'
    || target.tagName === 'SELECT'
    || target.isContentEditable
}

export function useFocusSearchShortcut(
  ref: RefObject<HTMLInputElement | null>,
  key = 'f',
) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== key) return
      if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return
      if (isEditableTarget(event.target)) return
      event.preventDefault()
      ref.current?.focus()
      ref.current?.select()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [ref, key])
}
