import { Button } from '@/shared/ui/button'
import { Robot } from '@phosphor-icons/react'

interface ProcessingButtonProps {
  onClick: () => void
  disabled?: boolean
}

export function ProcessingButton({ onClick, disabled }: ProcessingButtonProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      className="h-6 text-2xs gap-1 border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
      onClick={onClick}
      disabled={disabled}
    >
      <Robot className="w-3 h-3" />
      Process V2
    </Button>
  )
}
