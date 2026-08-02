import { cn } from '@/shared/lib/utils'

interface ScoreBadgeProps {
  label: string
  value: number | null
  className?: string
}

function scoreColor(value: number | null): string {
  if (value === null || value === undefined) return 'text-muted-foreground'
  if (value >= 90) return 'text-green-500'
  if (value >= 70) return 'text-emerald-500'
  if (value >= 50) return 'text-yellow-500'
  if (value >= 30) return 'text-orange-500'
  return 'text-red-500'
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
