import { Star } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'

interface FavoriteButtonProps {
  favorite: boolean
  onToggle: () => void
}

export function FavoriteButton({ favorite, onToggle }: FavoriteButtonProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={onToggle}
            aria-label={favorite ? 'Remove from favorites' : 'Add to favorites'}
            aria-pressed={favorite}
          >
            <Star
              className={cn('w-3.5 h-3.5', favorite ? 'text-yellow-500' : 'text-muted-foreground')}
              weight={favorite ? 'fill' : 'regular'}
            />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          {favorite ? 'Remove from favorites' : 'Add to favorites'}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
