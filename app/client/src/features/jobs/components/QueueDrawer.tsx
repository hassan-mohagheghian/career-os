import { useState } from 'react'
import {
  X, Clock, Stack, Gear, Buildings
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Drawer, DrawerHeader, DrawerContent } from '@/shared/components/Drawer'
import ProcessingItem from '@/shared/components/ProcessingItem'
import JobCreatedCard from './JobCreatedCard'
import JobProcessingCard from './JobProcessingCard'
import JobFailedCard from './JobFailedCard'

export default function QueueDrawer({
  open,
  onOpenChange,
  pending,
  collapsedSections,
  setCollapsedSections,
  deletePending,
  processPending,
  resetPending,
  pausePending,
  openWorkflow,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  pending: any[]
  collapsedSections: Record<string, boolean>
  setCollapsedSections: (fn: (prev: Record<string, boolean>) => Record<string, boolean>) => void
  deletePending: (id: number) => void
  processPending: (id: number) => void
  resetPending: (id: number) => void
  pausePending: (id: number) => void
  openWorkflow: (item: any) => void
}) {
  const [dragId, setDragId] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const createdCount = pending.filter(p => p.status === 'created').length
  const pendingCount = pending.filter(p => p.status === 'pending').length
  const queuedCount = pending.filter(p => p.status === 'queued').length
  const processingCount = pending.filter(p => p.status === 'processing').length
  const failedCount = pending.filter(p => p.status === 'failed' || p.status === 'cancelled').length
  const stackedTotal = createdCount + pendingCount + queuedCount + processingCount + failedCount

  const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
  const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
  const handleDragLeave = () => { setDragOverCol(null) }
  const handleDrop = (e, colId) => {
    e.preventDefault(); setDragOverCol(null)
    if (!dragId) return
    if (colId === 'created') resetPending(dragId)
    else if (colId === 'pending') processPending(dragId)
    else if (colId === 'queued') processPending(dragId)
    else if (colId === 'processing') processPending(dragId)
    setDragId(null)
  }

  const sections = [
    { id: 'created', count: createdCount, label: 'Created', icon: <Clock className="w-3 h-3" />, iconClass: 'text-gray-500', bgClass: 'bg-gradient-to-r from-gray-500/10 to-gray-500/5', borderClass: 'border-b border-gray-500/20', textClass: 'text-gray-600 dark:text-gray-400' },
    { id: 'pending', count: pendingCount, label: 'Pending', icon: <Clock className="w-3 h-3" />, iconClass: 'text-sky-500', bgClass: 'bg-gradient-to-r from-sky-500/10 to-sky-500/5', borderClass: 'border-b border-sky-500/20', textClass: 'text-sky-600 dark:text-sky-400' },
    { id: 'queued', count: queuedCount, label: 'Queued', icon: <Stack className="w-3 h-3" />, iconClass: 'text-yellow-500', bgClass: 'bg-gradient-to-r from-yellow-500/10 to-yellow-500/5', borderClass: 'border-b border-yellow-500/20', textClass: 'text-yellow-600 dark:text-yellow-500' },
    { id: 'processing', count: processingCount, label: 'Processing', icon: <Gear className="w-3 h-3" />, iconClass: 'text-blue-500', bgClass: 'bg-gradient-to-r from-blue-500/10 to-blue-500/5', borderClass: 'border-b border-blue-500/20', textClass: 'text-blue-600 dark:text-blue-500' },
    { id: 'failed', count: failedCount, label: 'Failed/Cancelled', icon: <X className="w-3 h-3" />, iconClass: 'text-red-500', bgClass: 'bg-gradient-to-r from-red-500/10 to-red-500/5', borderClass: 'border-b border-red-500/20', textClass: 'text-red-600 dark:text-red-500' },
  ]

  return (
    <Drawer open={open} onOpenChange={onOpenChange} variant="lg">
      <DrawerHeader title="Processing Queue" onClose={() => onOpenChange(false)} />
      <DrawerContent className="space-y-2">
        {sections.map(s => {
          const isEmpty = s.count === 0
          const isOpen = isEmpty ? false : !collapsedSections[s.id]
          return (
            <div key={s.id} className={cn("flex flex-col rounded-lg border overflow-hidden", isOpen ? "flex-1" : "")}>
              <div onClick={() => !isEmpty && setCollapsedSections(prev => ({ ...prev, [s.id]: !prev[s.id] }))}
                className={cn("px-3 py-1.5 flex items-center gap-1.5 shrink-0 transition cursor-pointer select-none hover:bg-muted/50", s.bgClass, s.borderClass)}>
                <span className={s.iconClass}>{s.icon}</span>
                <span className={cn("font-semibold text-xs uppercase tracking-wider", s.textClass)}>{s.label}</span>
                <Badge variant="secondary" className={cn("text-2xs h-4 ml-auto", isEmpty && "opacity-50")}>{s.count}</Badge>
                {!isEmpty && <span className="text-2xs text-muted-foreground">{isOpen ? '▾' : '▸'}</span>}
              </div>
              {isOpen && s.id === 'created' && (
                <ScrollArea className="max-h-48"
                  onDragOver={e => handleDragOver(e, 'created')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'created')}>
                  <div className="p-1.5 space-y-1">
                    {pending.filter(p => p.status === 'created').map(p =>
                      <JobCreatedCard key={p.num} item={p} onProcess={() => processPending(p.num)} onDelete={() => deletePending(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                  </div>
                </ScrollArea>
              )}
              {isOpen && s.id === 'pending' && (
                <ScrollArea className="max-h-48"
                  onDragOver={e => handleDragOver(e, 'pending')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'pending')}>
                  <div className="p-1.5 space-y-1">
                    {pending.filter(p => p.status === 'pending').map(p =>
                      <ProcessingItem key={p.num} item={p} onProcess={() => processPending(p.num)} onDelete={() => deletePending(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                  </div>
                </ScrollArea>
              )}
              {isOpen && s.id === 'queued' && (
                <ScrollArea className="max-h-48"
                  onDragOver={e => handleDragOver(e, 'queued')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'queued')}>
                  <div className="p-1.5 space-y-1">
                    {pending.filter(p => p.status === 'queued').map(p =>
                      <ProcessingItem key={p.num} item={p} onProcess={() => processPending(p.num)} onDelete={() => deletePending(p.num)} onMoveToCreated={() => resetPending(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                  </div>
                </ScrollArea>
              )}
              {isOpen && s.id === 'processing' && (
                <ScrollArea className="max-h-48"
                  onDragOver={e => handleDragOver(e, 'processing')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'processing')}>
                  <div className="p-1.5 space-y-1">
                    {pending.filter(p => p.status === 'processing').map(p =>
                      <JobProcessingCard key={p.num} item={p} onDragStart={e => handleDragStart(e, p.num)}
                        onCancel={() => pausePending(p.num)} onViewWorkflow={openWorkflow} />)}
                  </div>
                </ScrollArea>
              )}
              {isOpen && s.id === 'failed' && (
                <ScrollArea className="max-h-48">
                  <div className="p-1.5 space-y-1">
                    {pending.filter(p => p.status === 'failed' || p.status === 'cancelled').map(p =>
                      <JobFailedCard key={p.num} item={p} onDelete={() => deletePending(p.num)} onProcess={() => processPending(p.num)} onViewWorkflow={openWorkflow} />)}
                  </div>
                </ScrollArea>
              )}
            </div>
          )
        })}
        {stackedTotal === 0 && (
          <div className="text-center py-12 text-sm text-muted-foreground">
            <Buildings className="w-10 h-10 mx-auto mb-3 opacity-20" />
            No jobs are currently processing.
          </div>
        )}
      </DrawerContent>
    </Drawer>
  )
}
