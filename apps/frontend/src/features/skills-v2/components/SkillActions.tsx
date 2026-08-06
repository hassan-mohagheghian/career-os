import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { Eye, PencilSimple, Trash } from '@phosphor-icons/react'

interface SkillActionsProps {
  onViewDetails: () => void
  onEdit: () => void
  onDelete: () => void
}

function IconButton({
  icon,
  label,
  onClick,
  color,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  color?: string
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground" onClick={onClick} aria-label={label}>
          <span className={color}>{icon}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs">{label}</TooltipContent>
    </Tooltip>
  )
}

export function SkillActions({ onViewDetails, onEdit, onDelete }: SkillActionsProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex items-center gap-1">
        <IconButton icon={<Eye className="w-3 h-3" />} label="Details" onClick={onViewDetails} />
        <IconButton icon={<PencilSimple className="w-3 h-3" />} label="Edit" onClick={onEdit} />
        <IconButton icon={<Trash className="w-3 h-3 text-red-500" />} label="Delete" onClick={onDelete} />
      </div>
    </TooltipProvider>
  )
}
