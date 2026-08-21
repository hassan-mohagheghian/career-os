'use client'

import { useRef } from 'react'
import { DebouncedInput } from '@/shared/ui/debounced-input'
import { MagnifyingGlass } from '@phosphor-icons/react'
import { useFocusSearchShortcut } from '@/shared/hooks'

interface CitiesToolbarProps {
  query: string
  onQueryChange: (value: string) => void
}

export function CitiesToolbar({ query, onQueryChange }: CitiesToolbarProps) {
  const searchRef = useRef<HTMLInputElement>(null)
  useFocusSearchShortcut(searchRef)

  return (
    <div className="px-3 py-2 border-b border-border/40">
      <div className="relative flex-1 max-w-xs">
        <DebouncedInput
          ref={searchRef}
          value={query}
          onValueChange={onQueryChange}
          placeholder="Search city, country, original text…"
          icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
          wrapperClassName="w-full"
          inputClassName="pl-8 h-7 text-xs"
          aria-label="Search cities"
        />
      </div>
    </div>
  )
}