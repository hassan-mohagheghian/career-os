import { cn } from '@/shared/lib/utils'

const FAILED = new Set(['failed', 'error'])
const DONE = new Set(['completed', 'done', 'cancelled'])

export default function ProcessingCardFrame({ status, className, onDragStart, children }: {
  status: string
  className?: string
  onDragStart?: (e: React.DragEvent) => void
  children: React.ReactNode
}) {
  return (
    <div
      draggable={!!onDragStart}
      onDragStart={onDragStart}
      className={cn(
        'rounded-lg border bg-card p-1.5 min-w-0 overflow-hidden transition hover:shadow',
        FAILED.has(status) && 'border-red-500/30',
        DONE.has(status) && 'border-green-500/30',
        onDragStart && 'cursor-grab',
        className,
      )}
    >
      {children}
    </div>
  )
}
