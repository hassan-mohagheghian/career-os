'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleNotch, LinkBreak, LinkSimple, MagnifyingGlass } from '@phosphor-icons/react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { DebouncedInput } from '@/shared/ui/debounced-input'
import { companyApi } from '@/entities/company/api'
import type { CompanyDetail } from '@/entities/company/types'

interface RelateCompanyDialogProps {
  company: CompanyDetail | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onRelate: (companyId: string, mainCompanyId: string | null) => void
  pending: boolean
}

export function RelateCompanyDialog({ company, open, onOpenChange, onRelate, pending }: RelateCompanyDialogProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['companies-main-picker', query],
    queryFn: () => companyApi.listInfinite({ query: query || undefined, page_size: 20, sort: 'name', order: 'asc' }),
    enabled: open,
  })

  const candidates = (data?.items ?? []).filter((c) => c.id !== company?.id && !c.is_alias)

  const handleSelect = () => {
    if (!company || !selectedId) return
    onRelate(company.id, selectedId)
    setSelectedId(null)
    onOpenChange(false)
  }

  const handleUnrelate = () => {
    if (!company) return
    onRelate(company.id, null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LinkSimple className="w-5 h-5 text-primary" />
            Related Companies
          </DialogTitle>
          <DialogDescription>
            Relate <span className="font-semibold text-foreground">{company?.name || 'this company'}</span> to a main company.
            Jobs linked to an alias are re-pointed to the main company.
          </DialogDescription>
        </DialogHeader>

        {company?.is_alias && company.main_company && (
          <div className="flex items-center justify-between rounded-lg border border-border/40 bg-muted/10 px-3 py-2">
            <div className="flex items-center gap-2 min-w-0">
              <Badge variant="secondary" className="shrink-0 h-4 px-1.5 text-2xs text-muted-foreground">alias of</Badge>
              <span className="text-xs font-medium truncate">{company.main_company.name}</span>
            </div>
            <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs" onClick={handleUnrelate} disabled={pending}>
              <LinkBreak className="w-3 h-3" /> Remove
            </Button>
          </div>
        )}

        <div className="relative">
          <DebouncedInput
            value={query}
            onValueChange={(v) => { setQuery(v); setSelectedId(null) }}
            placeholder="Search companies..."
            icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
            clearable
            clearLabel="Clear search"
            wrapperClassName="w-full"
            inputClassName="pl-8 h-7 text-xs"
            aria-label="Search companies to relate"
          />
        </div>

        <div className="max-h-64 overflow-y-auto rounded-lg border border-border/40">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <CircleNotch className="w-5 h-5 text-muted-foreground animate-spin" />
            </div>
          )}
          {!isLoading && candidates.length === 0 && (
            <p className="py-8 text-center text-xs text-muted-foreground">No companies found.</p>
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
              {c.logo_url && <img src={c.logo_url} alt="" className="w-4 h-4 rounded shrink-0" />}
              <span className="font-medium truncate">{c.name}</span>
              {c.alias_count > 0 && (
                <span className="ml-auto shrink-0 text-2xs text-muted-foreground">{c.alias_count} alias</span>
              )}
            </button>
          ))}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSelect} disabled={!selectedId || pending} className="gap-1">
            <LinkSimple className="w-3.5 h-3.5" /> Set as Main
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
