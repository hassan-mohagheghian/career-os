import { cn } from '@/shared/lib/utils'

const GRADE_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  'A++': { bg: 'rgba(16,185,129,0.2)', text: '#10b981', border: 'border-emerald-400/30' },
  'A+': { bg: 'rgba(16,185,129,0.15)', text: '#34d399', border: 'border-emerald-500/30' },
  'A': { bg: 'rgba(34,197,94,0.12)', text: '#22c55e', border: 'border-green-500/30' },
  'A-': { bg: 'rgba(34,197,94,0.1)', text: '#4ade80', border: 'border-green-400/30' },
  'B+': { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa', border: 'border-blue-400/30' },
  'B': { bg: 'rgba(59,130,246,0.12)', text: '#3b82f6', border: 'border-blue-500/30' },
  'C': { bg: 'rgba(234,179,8,0.12)', text: '#eab308', border: 'border-yellow-500/30' },
  'D': { bg: 'rgba(239,68,68,0.12)', text: '#ef4444', border: 'border-red-500/30' },
}

interface GradeBadgeProps {
  grade: string | null | undefined
  className?: string
}

export function GradeBadge({ grade, className }: GradeBadgeProps) {
  if (!grade || grade === 'P') {
    return <span className={cn('inline-flex items-center text-xs text-muted-foreground', className)}>—</span>
  }
  const style = GRADE_STYLES[grade] || GRADE_STYLES['B']
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center w-8 h-6 rounded text-xs font-black border',
        style.border,
        className
      )}
      style={{ background: style.bg, color: style.text }}
    >
      {grade}
    </span>
  )
}
