'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleNotch, GitMerge, MagnifyingGlass } from '@phosphor-icons/react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { DebouncedInput } from '@/shared/ui/debounced-input'
import { skillApi } from '@/entities/skill/api'

interface MergeSkillDialogProps {
  sources: { id: number; name: string }[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onMerge: (targetId: number) => void
  pending: boolean
}

export function MergeSkillDialog({ sources, open, onOpenChange, onMerge, pending }: MergeSkillDialogProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const sourceIds = sources.map((s) => s.id)

  const { data, isLoading } = useQuery({
    queryKey: ['skills-merge-picker', query],
    queryFn: () => skillApi.listInfinite({ query: query || undefined, page_size: 20, sort: 'name', order: 'asc' }),
    enabled: open,
  })

  const candidates = (data?.items ?? []).filter((c) => !sourceIds.includes(c.id))

  const handleMerge = () => {
    if (sources.length === 0 || !selectedId) return
    onMerge(selectedId)
    setSelectedId(null)
    onOpenChange(false)
  }

  const sourceLabel =
    sources.length === 1
      ? sources[0]?.name ?? 'this skill'
      : `${sources.length} skills`

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader className="space-y-1.5">
          <DialogTitle className="flex items-center gap-2">
            <GitMerge className="w-5 h-5 text-primary" />
            Merge Skill{sources.length !== 1 ? 's' : ''}
          </DialogTitle>
          <DialogDescription>
            Merge <span className="font-semibold text-foreground">{sourceLabel}</span>
            {sources.length > 1 && (
              <span className="text-muted-foreground"> ({sources.map((s) => s.name).join(', ')})</span>
            )}{' '}
            into another skill. Mentions are re-pointed; the skill
            {sources.length !== 1 ? 's become' : ' becomes'} aliases of the target.
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          <DebouncedInput
            value={query}
            onValueChange={(v) => { setQuery(v); setSelectedId(null) }}
            placeholder="Search skills..."
            icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
            clearable
            clearLabel="Clear search"
            wrapperClassName="w-full"
            inputClassName="pl-8 h-7 text-xs"
            aria-label="Search skills to merge into"
          />
        </div>

        <div className="max-h-64 overflow-y-auto rounded-lg border border-border/40">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <CircleNotch className="w-5 h-5 text-muted-foreground animate-spin" />
            </div>
          )}
          {!isLoading && candidates.length === 0 && (
            <p className="py-8 text-center text-xs text-muted-foreground">No skills found.</p>
          )}
          {!isLoading && candidates.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setSelectedId(c.id)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-left text-xs transition-colors ${
                selectedId === c.id ? 'bg-primary/10' : 'hover:bg-muted/40'
              }`}
            >
              <span className="font-medium truncate">{c.name}</span>
              {c.mention_count > 0 && (
                <span className="ml-auto shrink-0 text-2xs text-muted-foreground">{c.mention_count} mention{c.mention_count !== 1 ? 's' : ''}</span>
              )}
            </button>
          ))}
        </div>

        <DialogFooter className="flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleMerge} disabled={!selectedId || pending} className="gap-1">
            <GitMerge className="w-3.5 h-3.5" /> Merge {sources.length > 1 ? `${sources.length} into selected` : 'into selected'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
