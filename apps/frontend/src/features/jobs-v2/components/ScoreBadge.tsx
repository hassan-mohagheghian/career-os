import { cn } from '@/shared/lib/utils'
import { scoreColor } from '@/shared/lib/grade'

interface ScoreBadgeProps {
  label: string
  value: number | null
  className?: string
}

export function ScoreBadge({ label, value, className }: ScoreBadgeProps) {
  return (
    <span className={cn('inline-flex items-center gap-1 text-xs', className)}>
      <span className="text-muted-foreground">{label}</span>
      <span className={cn('font-medium tabular-nums', scoreColor(value))}>
        {value !== null && value !== undefined ? value : '—'}
      </span>
    </span>
  )
}
