'use client'

import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/lib/utils'

export interface MultiSelectFilterOption<T extends string = string> {
  value: T
  label: string
}

interface MultiSelectFilterProps<T extends string = string> {
  label: string
  options: MultiSelectFilterOption<T>[]
  selected: T[]
  onChange: (values: T[]) => void
  className?: string
}

export function MultiSelectFilter<T extends string = string>({
  label,
  options,
  selected,
  onChange,
  className,
}: MultiSelectFilterProps<T>) {
  const selectedSet = new Set(selected)

  const toggle = (value: T) => {
    if (selectedSet.has(value)) {
      onChange(selected.filter((v) => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  const triggerLabel = selected.length
    ? selected.map((v) => options.find((o) => o.value === v)?.label ?? v).join(', ')
    : label

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            'inline-flex h-7 w-auto items-center gap-1 text-2xs text-primary',
            className,
          )}
          aria-label={`${label} filter`}
          aria-pressed={selected.length > 0}
        >
          <span>{triggerLabel}</span>
          {selected.length > 0 && (
            <span className="rounded-none bg-emerald-500/15 px-1 text-[10px] font-medium text-emerald-500">
              {selected.length}
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-56 p-1.5">
        <div className="flex max-h-72 flex-col gap-0.5 overflow-y-auto">
          {options.map((opt) => {
            const checked = selectedSet.has(opt.value)
            return (
              <div
                key={opt.value}
                role="button"
                tabIndex={0}
                onClick={() => toggle(opt.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    toggle(opt.value)
                  }
                }}
                className="flex cursor-pointer items-center gap-2 rounded-none px-1.5 py-1 text-2xs hover:bg-accent"
              >
                <Checkbox checked={checked} onCheckedChange={() => toggle(opt.value)} className="pointer-events-none" />
                <span>{opt.label}</span>
              </div>
            )
          })}
        </div>
        {selected.length > 0 && (
          <button
            type="button"
            onClick={() => onChange([])}
            className="mt-1 w-full rounded-none border-t border-border/40 pt-1.5 text-2xs text-muted-foreground hover:text-primary"
          >
            Clear
          </button>
        )}
      </PopoverContent>
    </Popover>
  )
}
