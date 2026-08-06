'use client'

import { CaretDown, ListChecks, Check } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/lib/utils'

export interface ColumnToggleOption {
  key: string
  label: string
  checked: boolean
}

interface ColumnsDropdownProps {
  options: ColumnToggleOption[]
  onToggle: (key: string, checked: boolean) => void
}

export function ColumnsDropdown({ options, onToggle }: ColumnsDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="h-7 w-auto gap-1 text-2xs">
          <ListChecks className="w-3 h-3" />
          Columns
          <CaretDown className="w-3 h-3 text-muted-foreground" weight="bold" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[12rem]">
        <DropdownMenuItem disabled className="text-2xs text-muted-foreground">
          Show columns
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {options.map((option) => (
          <DropdownMenuItem
            key={option.key}
            onClick={() => onToggle(option.key, !option.checked)}
            className={cn('cursor-pointer', option.checked && 'text-primary')}
          >
            <Check weight="bold" className={cn('w-3.5 h-3.5', option.checked ? 'opacity-100' : 'opacity-0')} />
            {option.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
