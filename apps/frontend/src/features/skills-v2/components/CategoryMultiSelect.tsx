'use client'

import { useState } from 'react'
import { CaretDown, Plus, CircleNotch, MagnifyingGlass, X } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Checkbox } from '@/shared/ui/checkbox'
import { Badge } from '@/shared/ui/badge'
import { categoryColorClass } from '@/entities/skill/categoryColors'

const MAX_TRIGGER_BADGES = 3

interface CategoryMultiSelectProps {
  value: string[]
  onChange: (next: string[]) => void
  options: string[]
  placeholder?: string
  icon?: React.ReactNode
  align?: 'start' | 'end'
  size?: 'sm' | 'md'
  disabled?: boolean
  searchable?: boolean
  onCreate?: (name: string) => Promise<{ name: string } | string | void>
  createPlaceholder?: string
}

export function CategoryMultiSelect({
  value,
  onChange,
  options,
  placeholder = 'Category',
  icon,
  align = 'start',
  size = 'sm',
  disabled = false,
  searchable = true,
  onCreate,
  createPlaceholder = 'Add category...',
}: CategoryMultiSelectProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const toggle = (category: string) => {
    onChange(value.includes(category) ? value.filter((v) => v !== category) : [...value, category])
  }

  const normalizedSearch = search.trim().toLowerCase()
  const filteredOptions = normalizedSearch
    ? options.filter((c) => c.toLowerCase().includes(normalizedSearch))
    : options

  const handleCreate = async () => {
    const name = newName.trim()
    if (!name || !onCreate || creating) return
    if (value.includes(name)) {
      setNewName('')
      return
    }
    setCreating(true)
    setCreateError(null)
    try {
      const result = await onCreate(name)
      const createdName = typeof result === 'string' ? result : (result && 'name' in result ? result.name : name)
      onChange([...value, createdName ?? name])
      setNewName('')
    } catch {
      setCreateError('Failed to add category')
    } finally {
      setCreating(false)
    }
  }

  const heightClass = size === 'sm' ? 'h-7' : 'h-8'
  const selectedCount = value.length
  const visibleBadges = value.slice(0, MAX_TRIGGER_BADGES)
  const hiddenCount = Math.max(0, selectedCount - visibleBadges.length)

  return (
    <Popover open={open} onOpenChange={(next) => { setOpen(next); if (!next) setSearch('') }}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          className={cn(
            heightClass,
            'w-auto gap-1 text-2xs border-dashed font-normal',
            selectedCount > 0 && 'border-emerald-500/50 text-primary',
          )}
          aria-label="Filter by category"
        >
          {icon && <span className="shrink-0">{icon}</span>}
          {selectedCount === 0 ? (
            <span className="text-muted-foreground">{placeholder}</span>
          ) : (
            <span className="flex items-center gap-1 min-w-0">
              {visibleBadges.map((cat) => (
                <Badge key={cat} variant="outline" className={cn('h-4 px-1.5 text-2xs border-transparent shrink-0', categoryColorClass(cat))}>
                  {cat}
                </Badge>
              ))}
              {hiddenCount > 0 && <span className="text-2xs text-muted-foreground shrink-0">+{hiddenCount}</span>}
            </span>
          )}
          <CaretDown className="h-2 w-2 opacity-50 shrink-0" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align={align} className="w-56 p-0">
        <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
          <span className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">
            Categories {selectedCount > 0 && `(${selectedCount})`}
          </span>
          {selectedCount > 0 && (
            <button
              type="button"
              className="text-2xs text-emerald-500 hover:underline"
              onClick={() => onChange([])}
            >
              Clear
            </button>
          )}
        </div>
        {searchable && options.length > 0 && (
          <div className="px-2 py-1.5 border-b border-border/40">
            <div className="relative">
              <MagnifyingGlass className="w-3 h-3 text-muted-foreground absolute left-2 top-1/2 -translate-y-1/2" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search categories..."
                className="h-7 pl-6 pr-7 text-2xs"
                aria-label="Search categories"
              />
              {search && (
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setSearch('')}
                  aria-label="Clear category search"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        )}
        <ScrollArea className="h-40">
          <div className="p-1">
            {options.length === 0 ? (
              <p className="px-2 py-3 text-2xs text-muted-foreground">No categories yet.</p>
            ) : filteredOptions.length === 0 ? (
              <p className="px-2 py-3 text-2xs text-muted-foreground">No categories match "{search}".</p>
            ) : (
              filteredOptions.map((category) => {
                const checked = value.includes(category)
                return (
                  <label
                    key={category}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1.5 text-2xs cursor-pointer rounded-sm transition-colors',
                      checked && 'bg-emerald-500/5',
                    )}
                    onClick={() => toggle(category)}
                  >
                    <Checkbox checked={checked} className="h-3 w-3" />
                    <Badge variant="outline" className={cn('h-4 px-1.5 text-2xs border-transparent', categoryColorClass(category))}>
                      {category}
                    </Badge>
                  </label>
                )
              })
            )}
          </div>
        </ScrollArea>
        {onCreate && (
          <div className="border-t border-border/40 p-2">
            <div className="flex items-center gap-1">
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleCreate() } }}
                placeholder={createPlaceholder}
                className="h-7 text-2xs"
                aria-label="New category name"
              />
              <Button
                type="button"
                size="icon"
                variant="outline"
                className="h-7 w-7 shrink-0"
                onClick={handleCreate}
                disabled={creating || !newName.trim()}
                aria-label="Add category"
              >
                {creating ? <CircleNotch className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
              </Button>
            </div>
            {createError && <p className="mt-1 text-2xs text-destructive">{createError}</p>}
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
