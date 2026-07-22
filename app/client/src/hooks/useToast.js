import { useState, useEffect, useCallback } from 'react'

export function useToast() {
  const [toast, setToast] = useState(null)

  useEffect(() => {
    const handler = (e) => {
      setToast(e.detail)
      setTimeout(() => setToast(null), 2000)
    }
    window.addEventListener('toast', handler)
    return () => window.removeEventListener('toast', handler)
  }, [])

  const showToast = useCallback((msg) => {
    setToast(msg)
    if (msg) setTimeout(() => setToast(null), 2000)
  }, [])

  return { toast, showToast }
}
