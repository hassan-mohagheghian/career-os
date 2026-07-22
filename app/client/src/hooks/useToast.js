import { useEffect } from 'react'
import { toast } from 'sonner'

export function useToast() {
  useEffect(() => {
    const handler = (e) => {
      if (e.detail) {
        toast.success(e.detail)
      }
    }
    window.addEventListener('toast', handler)
    return () => window.removeEventListener('toast', handler)
  }, [])

  return { toast }
}
