import { cn } from '@/shared/lib/utils'

interface RankBadgeProps {
  rank: number | null
  className?: string
}

export function RankBadge({ rank, className }: RankBadgeProps) {
  if (rank == null) return null
  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div className="text-lg font-bold text-foreground">#{rank}</div>
      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">
        Rank
      </div>
    </div>
  )
}
