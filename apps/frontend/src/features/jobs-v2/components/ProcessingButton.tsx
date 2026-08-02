import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/shared/ui/tooltip'
import { Robot } from '@phosphor-icons/react'

interface ProcessingButtonProps {
  onClick: () => void
  disabled?: boolean
}

export function ProcessingButton({ onClick, disabled }: ProcessingButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-6 w-6 p-0 border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
          onClick={onClick}
          disabled={disabled}
          aria-label="Process"
        >
          <Robot className="w-3 h-3" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs">Process</TooltipContent>
    </Tooltip>
  )
}