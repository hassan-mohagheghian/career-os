import { useEffect } from 'react'
import { toast } from 'sonner'

export function useToast() {
  useEffect(() => {
    const handler = (e: CustomEvent<string>) => {
      if (e.detail) {
        toast.success(e.detail)
      }
    }
    window.addEventListener('toast', handler as EventListener)
    return () => window.removeEventListener('toast', handler as EventListener)
  }, [])

  return { toast }
}
