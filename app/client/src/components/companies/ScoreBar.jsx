import { cn } from '@/lib/utils'

export default function ScoreBar({ label, value, max = 100 }) {
  const pct = Math.min(100, Math.max(0, (value || 0) / max * 100))
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-blue-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground w-20 shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-bold w-8 text-right">{value ?? '?'}</span>
    </div>
  )
}
