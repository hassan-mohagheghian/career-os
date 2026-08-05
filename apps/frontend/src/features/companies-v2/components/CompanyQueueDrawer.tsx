'use client'

import { useMemo } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Button } from '@/shared/ui/button'
import { CircleNotch, Play, Trash, X, Clock, Stack, Gear, Note, LinkSimple } from '@phosphor-icons/react'
import type { PendingCompany } from '@/entities/company/types'
import { usePendingCompaniesQuery, usePendingProcessMutation, usePendingDeleteMutation } from '@/entities/company/hooks'
import { toast } from 'sonner'

interface CompanyQueueDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function parseNotes(item: PendingCompany): Array<{ type?: string; content?: string; title?: string }> {
  const raw = item.notes
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function QueueItem({
  item,
  onProcess,
  onDelete,
  showProcess,
}: {
  item: PendingCompany
  onProcess: () => void
  onDelete: () => void
  showProcess: boolean
}) {
  const notes = parseNotes(item)

  return (
    <div className="flex items-start gap-3 p-2 rounded-lg border border-border/40 bg-muted/20 min-w-0 overflow-hidden">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-foreground truncate">
          {item.name || item.input_text || item.notes || `Company #${item.id}`}
        </p>
        <p className="text-2xs text-muted-foreground truncate">
          {item.current_node ? `Step: ${item.current_node}` : item.status}
          {item.error && <span className="text-red-500"> — {item.error}</span>}
        </p>
        {notes.length > 0 && (
          <div className="space-y-0.5 mt-1">
            {notes.slice(0, 4).map((note, i) => {
              const isUrl = note.type === 'url' || (note.content ?? '').startsWith('http')
              return (
                <div key={i} className="flex items-start gap-1 text-2xs text-muted-foreground min-w-0">
                  {isUrl ? <LinkSimple className="w-2.5 h-2.5 shrink-0 mt-0.5 text-primary" /> : <Note className="w-2.5 h-2.5 shrink-0 mt-0.5" />}
                  {isUrl ? (
                    <a href={note.content} target="_blank" rel="noreferrer" className="text-primary hover:underline break-all">{note.content}</a>
                  ) : (
                    <span className="truncate">{note.content}</span>
                  )}
                </div>
              )
            })}
            {notes.length > 4 && (
              <p className="text-2xs text-muted-foreground">+{notes.length - 4} more</p>
            )}
          </div>
        )}
      </div>
      <div className="shrink-0 flex items-center gap-1 pt-0.5">
        {showProcess && (
          <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 text-emerald-500 hover:bg-emerald-500/10" onClick={onProcess} title="Process">
            <Play className="w-3 h-3" />
          </Button>
        )}
        <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 text-destructive hover:bg-destructive/10" onClick={onDelete} title="Delete">
          <Trash className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}

function QueueSection({
  title,
  icon,
  items,
  color,
  showProcess,
  onProcess,
  onDelete,
  emptyText,
}: {
  title: string
  icon: React.ReactNode
  items: PendingCompany[]
  color: string
  showProcess: boolean
  onProcess: (id: number | string) => void
  onDelete: (id: number | string) => void
  emptyText: string
}) {
  return (
    <div>
      <h3 className={`text-xs font-semibold uppercase tracking-wide ${color} px-4 py-2 flex items-center gap-1`}>
        {icon}{title} ({items.length})
      </h3>
      {items.length === 0 ? (
        <p className="text-2xs text-muted-foreground px-4 pb-2">{emptyText}</p>
      ) : (
        <div className="space-y-2 px-4">
          {items.map(item => (
            <QueueItem
              key={String(item.id)}
              item={item}
              showProcess={showProcess}
              onProcess={() => onProcess(item.id)}
              onDelete={() => onDelete(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function CompanyQueueDrawer({ open, onOpenChange }: CompanyQueueDrawerProps) {
  const { data: items, isLoading, isError } = usePendingCompaniesQuery()
  const processMutation = usePendingProcessMutation()
  const deleteMutation = usePendingDeleteMutation()

  const {
    created, pending, queued, processing, running, failed,
  } = useMemo(() => {
    const list = items ?? []
    return {
      created: list.filter(i => i.status === 'created'),
      pending: list.filter(i => i.status === 'pending'),
      queued: list.filter(i => i.status === 'queued'),
      processing: list.filter(i => i.status === 'processing'),
      running: list.filter(i => i.status === 'running'),
      failed: list.filter(i => i.status === 'failed' || i.status === 'cancelled'),
    }
  }, [items])

  const total = (items ?? []).length

  const handleProcess = (id: number | string) => {
    processMutation.mutate(id, {
      onSuccess: () => toast.success('Company queued for processing'),
      onError: () => toast.error('Failed to queue company'),
    })
  }

  const handleDelete = (id: number | string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => toast.success('Pending company deleted'),
      onError: () => toast.error('Failed to delete pending company'),
    })
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold">Company Queue ({total})</SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0 min-w-0">
          {isLoading && (
            <div className="flex items-center justify-center h-40">
              <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
            </div>
          )}
          {isError && !isLoading && (
            <div className="flex items-center justify-center h-40">
              <p className="text-sm text-red-500">Unable to load the company queue.</p>
            </div>
          )}
          {!isLoading && !isError && (
            <div className="py-2 space-y-4 min-w-0">
              <QueueSection title="Created" icon={<Clock className="w-3 h-3" />} items={created} color="text-gray-500" showProcess onProcess={handleProcess} onDelete={handleDelete} emptyText="No companies in this state." />
              <QueueSection title="Pending" icon={<Note className="w-3 h-3" />} items={pending} color="text-sky-500" showProcess onProcess={handleProcess} onDelete={handleDelete} emptyText="No companies in this state." />
              <QueueSection title="Queued" icon={<Stack className="w-3 h-3" />} items={queued} color="text-yellow-500" showProcess={false} onProcess={handleProcess} onDelete={handleDelete} emptyText="No companies in this state." />
              <QueueSection title="Processing" icon={<Gear className="w-3 h-3" />} items={[...processing, ...running]} color="text-blue-500" showProcess={false} onProcess={handleProcess} onDelete={handleDelete} emptyText="No companies in this state." />
              <QueueSection title="Failed / Cancelled" icon={<X className="w-3 h-3" />} items={failed} color="text-red-500" showProcess onProcess={handleProcess} onDelete={handleDelete} emptyText="No companies in this state." />
            </div>
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
