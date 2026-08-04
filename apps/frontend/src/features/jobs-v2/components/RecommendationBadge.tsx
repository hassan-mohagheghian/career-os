import { cn } from '@/shared/lib/utils'

interface RecommendationBadgeProps {
  recommendation: string | null
  className?: string
}

const recommendationConfig: Record<string, { color: string; label: string }> = {
  apply: { color: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20', label: 'Apply' },
  consider: { color: 'bg-amber-500/15 text-amber-500 border-amber-500/20', label: 'Consider' },
  skip: { color: 'bg-gray-500/15 text-gray-500 border-gray-500/20', label: 'Skip' },
}

export function RecommendationBadge({ recommendation, className }: RecommendationBadgeProps) {
  if (!recommendation) {
    return (
      <span className={cn('inline-flex items-center text-xs text-muted-foreground', className)}>
        —
      </span>
    )
  }

  const config = recommendationConfig[recommendation] || {
    color: 'bg-gray-500/15 text-gray-500 border-gray-500/20',
    label: recommendation,
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-medium border capitalize',
      config.color,
      className
    )}>
      {config.label}
    </span>
  )
}
