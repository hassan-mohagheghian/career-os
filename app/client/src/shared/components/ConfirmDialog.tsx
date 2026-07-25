import { useState } from 'react'
import { cn } from '@/shared/lib/utils'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from '@/shared/ui/alert-dialog'

export default function ConfirmDialog({ dialog, onClose }) {
  if (!dialog) return null

  return (
    <AlertDialog open={!!dialog} onOpenChange={(open) => { if (!open) { dialog.resolve(false); onClose() } }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{dialog.title}</AlertDialogTitle>
          <AlertDialogDescription>{dialog.message}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => { dialog.resolve(false); onClose() }}>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={() => { dialog.resolve(true); onClose() }}
            className={cn(dialog.variant === 'warning' ? 'bg-yellow-500 hover:bg-yellow-600' : dialog.variant === 'info' ? '' : 'bg-destructive hover:bg-destructive/90')}>
            {dialog.confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export function useConfirmDialog() {
  const [dialog, setDialog] = useState(null)

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  return { dialog, showConfirm, onClose: () => setDialog(null) }
}
