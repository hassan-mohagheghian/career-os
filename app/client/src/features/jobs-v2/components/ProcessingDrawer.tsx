'use client'

import { useMemo } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Button } from '@/shared/ui/button'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { X, CircleNotch, Clock, CheckCircle, XCircle } from '@phosphor-icons/react'
import type { JobListItem, ProcessingStatus } from '@/entities/job/types'

interface ProcessingDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  jobs: JobListItem[]
}

interface QueueEntry {
  id: string
  jobId: string
  title: string
  status: 'running' | 'waiting' | 'completed' | 'failed'
  step?: string
  progress?: number
  error?: string
}

function toQueueEntry(job: JobListItem): QueueEntry | null {
  const exec = job.latest_processing_execution
  if (!exec) return null

  const statusMap: Record<string, 'running' | 'waiting' | 'completed' | 'failed'> = {
    queued: 'waiting',
    starting: 'waiting',
    running: 'running',
    completed: 'completed',
    failed: 'failed',
    cancelled: 'failed',
    created: 'waiting',
  }

  return {
    id: exec.id,
    jobId: job.id,
    title: job.title || 'Untitled',
    status: statusMap[exec.status] || 'waiting',
    progress: undefined,
  }
}

function StatusIcon({ status }: { status: QueueEntry['status'] }) {
  switch (status) {
    case 'running': return <CircleNotch className="w-4 h-4 text-emerald-500 animate-spin" />
    case 'waiting': return <Clock className="w-4 h-4 text-blue-500" />
    case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
  }
}

function QueueSection({ title, items }: { title: string; items: QueueEntry[] }) {
  if (items.length === 0) return null

  return (
    <div>
      <h3 className="text-xs font-medium text-muted-foreground px-4 py-2">{title} ({items.length})</h3>
      <div className="space-y-1 px-4">
        {items.map(item => (
          <div key={item.id} className="flex items-start gap-3 p-2 rounded-lg border border-border/40 bg-muted/20">
            <StatusIcon status={item.status} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{item.title}</p>
              {item.progress !== undefined && (
                <div className="w-full h-1.5 bg-muted rounded-full mt-1.5 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ProcessingDrawer({ open, onOpenChange, jobs }: ProcessingDrawerProps) {
  const entries: QueueEntry[] = useMemo(() => {
    return jobs.map(toQueueEntry).filter((e): e is QueueEntry => e !== null)
  }, [jobs])

  const running = entries.filter(i => i.status === 'running')
  const waiting = entries.filter(i => i.status === 'waiting')
  const failed = entries.filter(i => i.status === 'failed')
  const completed = entries.filter(i => i.status === 'completed')

  const totalActive = running.length + waiting.length

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[480px] p-0">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40">
          <SheetTitle className="text-sm font-semibold">Processing Queue</SheetTitle>
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => onOpenChange(false)}>
            <X className="w-4 h-4" />
          </Button>
        </SheetHeader>
        <ScrollArea className="flex-1 h-[calc(100vh-60px)]">
          {totalActive === 0 && failed.length === 0 && completed.length === 0 ? (
            <div className="flex items-center justify-center h-40">
              <p className="text-sm text-muted-foreground">No Processing Executions are currently running.</p>
            </div>
          ) : (
            <div className="py-2 space-y-4">
              {running.length > 0 && <QueueSection title="Running" items={running} />}
              {waiting.length > 0 && <QueueSection title="Waiting" items={waiting} />}
              {failed.length > 0 && <QueueSection title="Failed" items={failed} />}
              {completed.length > 0 && <QueueSection title="Completed" items={completed} />}
            </div>
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
