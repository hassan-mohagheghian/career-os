import { cn } from '@/shared/lib/utils'

interface RankBadgeProps {
  rank: number | null
  className?: string
  /** `detail` (default) is the large badge for drawers; `inline` matches the
   *  compact list `ScoreBadge` styling. */
  variant?: 'detail' | 'inline'
}

export function RankBadge({ rank, className, variant = 'detail' }: RankBadgeProps) {
  if (rank == null) return null
  if (variant === 'inline') {
    return (
      <span
        data-testid="job-rank"
        className={cn('inline-flex items-center gap-1 text-xs', className)}
      >
        <span className="text-muted-foreground">#</span>
        <span className="font-medium tabular-nums text-foreground">{rank}</span>
      </span>
    )
  }
  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div className="text-lg font-bold text-foreground">#{rank}</div>
      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">
        Rank
      </div>
    </div>
  )
}
