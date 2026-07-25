import { useState, useEffect, useRef } from 'react'
import { CaretDown } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'

export function MultiSelect({ value, onChange, options, placeholder, alignRight, icon }) {
  const [open, setOpen] = useState(false)
  const hasValue = value.length > 0

  const toggle = (v) => {
    onChange(value.includes(v) ? value.filter(x => x !== v) : [...value, v])
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "h-6 px-2 text-[0.6rem] gap-1 whitespace-nowrap border-dashed",
            hasValue && "border-green-500/50 text-green-500 bg-green-500/5"
          )}
        >
          {icon && <span className="flex-shrink-0">{icon}</span>}
          {hasValue ? `${value.length} sel` : placeholder}
          <CaretDown className="h-2 w-2 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align={alignRight ? "end" : "start"}
        className="w-40 p-0"
      >
        <ScrollArea className="h-40">
          <div className="p-1">
            {options.map(o => {
              const checked = value.includes(o.value)
              return (
                <label
                  key={o.value}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 text-[0.6rem] cursor-pointer rounded-sm transition-colors",
                    checked && "bg-green-500/5"
                  )}
                  onClick={() => toggle(o.value)}
                >
                  <Checkbox checked={checked} className="h-3 w-3" />
                  {o.icon && <span>{o.icon}</span>}
                  <span className={cn(checked && "font-semibold")}>{o.label}</span>
                </label>
              )
            })}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
}
