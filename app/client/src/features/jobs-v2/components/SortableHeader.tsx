import { Popover, PopoverTrigger, PopoverContent } from '@/shared/ui/popover'
import { cn } from '@/shared/lib/utils'
import { CaretUp, CaretDown, ArrowsDownUp } from '@phosphor-icons/react'

export interface ScoreSortOption {
  field: string
  label: string
}

interface SortableHeaderProps {
  label: string
  field?: string
  scoreOptions?: ScoreSortOption[]
  sort: string
  order: 'asc' | 'desc'
  onSortChange: (field: string) => void
  className?: string
}

function OrderIcon({ active, order }: { active: boolean; order: 'asc' | 'desc' }) {
  if (!active) return <ArrowsDownUp className="w-3 h-3 opacity-40" />
  return order === 'desc' ? <CaretDown className="w-3 h-3" /> : <CaretUp className="w-3 h-3" />
}

export function SortableHeader({
  label, field, scoreOptions, sort, order, onSortChange, className,
}: SortableHeaderProps) {
  if (scoreOptions) {
    const activeOption = scoreOptions.find(o => o.field === sort)
    return (
      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            className={cn(
              'inline-flex items-center gap-1 text-2xs font-medium uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors',
              activeOption && 'text-foreground',
              className
            )}
          >
            {label}
            <OrderIcon active={!!activeOption} order={order} />
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-44 p-1.5">
          <p className="px-2 py-1 text-2xs uppercase tracking-wider text-muted-foreground">Sort by score</p>
          {scoreOptions.map(option => {
            const active = sort === option.field
            return (
              <button
                key={option.field}
                type="button"
                onClick={() => onSortChange(option.field)}
                className={cn(
                  'w-full flex items-center justify-between px-2 py-1.5 rounded text-xs text-left hover:bg-muted/50 transition-colors',
                  active && 'text-emerald-500 font-medium'
                )}
              >
                <span>{option.label}</span>
                <OrderIcon active={active} order={order} />
              </button>
            )
          })}
        </PopoverContent>
      </Popover>
    )
  }

  if (!field) return <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">{label}</span>

  return (
    <button
      type="button"
      onClick={() => onSortChange(field)}
      className={cn(
        'inline-flex items-center gap-1 text-2xs font-medium uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors',
        sort === field && 'text-foreground',
        className
      )}
    >
      {label}
      <OrderIcon active={sort === field} order={order} />
    </button>
  )
}
