'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { CircleNotch, Clock, CheckCircle, XCircle, CaretRight, CaretDown } from '@phosphor-icons/react'
import LinkDisplay from '@/shared/components/LinkDisplay'
import { processingApi } from '@/entities/processing/api'
import { mergeWorkflowStep } from '@/entities/processing/workflowMerge'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { QueueEntry, QueueSnapshot, WorkflowStep, WorkflowProgress } from '@/entities/processing/types'

interface ProcessingDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  reloadKey?: number
}

function stepStatusIcon(status: WorkflowStep['status']) {
  switch (status) {
    case 'processing': return <CircleNotch className="w-3.5 h-3.5 text-emerald-500 animate-spin shrink-0" />
    case 'completed': return <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0" />
    case 'failed': return <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
    case 'skipped': return <Clock className="w-3.5 h-3.5 text-muted-foreground/50 shrink-0" />
    default: return <Clock className="w-3.5 h-3.5 text-blue-500 shrink-0" />
  }
}

function WorkflowStepItem({ step, depth }: { step: WorkflowStep; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 1)
  const hasChildren = step.children.length > 0

  return (
    <div className="min-w-0">
      <button
        type="button"
        className="w-full min-w-0 flex items-start gap-2 text-left p-1.5 rounded hover:bg-muted/40"
        style={{ paddingLeft: `${depth * 16 + 6}px` }}
        onClick={() => hasChildren && setExpanded(e => !e)}
      >
        {hasChildren ? (
          expanded
            ? <CaretDown className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
            : <CaretRight className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        {stepStatusIcon(step.status)}
        <div className="flex-1 min-w-0 overflow-hidden">
          <div className="flex items-center justify-between gap-2 min-w-0">
            <p className="text-xs font-medium text-foreground min-w-0 break-words">{step.title}</p>
            {step.progress !== null && step.progress !== undefined && (
              <span className="text-2xs text-muted-foreground shrink-0">{Math.round(step.progress)}%</span>
            )}
          </div>
          {step.progress !== null && step.progress !== undefined && (
            <div className="w-full h-1 bg-muted rounded-full mt-1 overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, step.progress))}%` }}
              />
            </div>
          )}
          {step.error && (
            <p className="text-2xs text-red-500 mt-1 break-words">{step.error.message}</p>
          )}
        </div>
      </button>
      {expanded && hasChildren && (
        <div>
          {step.children.map(child => (
            <WorkflowStepItem key={child.id} step={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function WorkflowPanel({ workflow, entry }: { workflow: WorkflowProgress | null; entry: QueueEntry }) {
  const steps = workflow?.steps ?? []

  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-1 min-w-0">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-foreground min-w-0 truncate">{workflow?.name ?? 'Workflow'}</p>
        {workflow?.progress !== null && workflow?.progress !== undefined && (
          <span className="text-2xs text-muted-foreground shrink-0">{Math.round(workflow.progress)}%</span>
        )}
      </div>
      {workflow?.progress !== null && workflow?.progress !== undefined && (
        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, workflow.progress))}%` }}
          />
        </div>
      )}
      <div className="pt-1 min-w-0">
        {steps.length === 0 ? (
          <p className="text-2xs text-muted-foreground">No steps recorded yet.</p>
        ) : (
          steps.map(step => <WorkflowStepItem key={step.id} step={step} depth={0} />)
        )}
      </div>
      {entry.error && (
        <p className="text-2xs text-red-500 pt-1 break-words">{entry.error}</p>
      )}
    </div>
  )
}

function EntryLinks({ entry }: { entry: QueueEntry }) {
  const links = [
    ...(entry.url ? [{ url: entry.url }] : []),
    ...(entry.links ?? []),
  ]
  if (links.length === 0) return null
  return (
    <div className="space-y-0.5 mt-1.5 px-1">
      {links.map((link, i) => (
        <LinkDisplay key={`${link.url}-${i}`} url={link.url} title={link.title} maxLength={48} />
      ))}
    </div>
  )
}

function QueueSection({
  title,
  items,
  color,
  renderDetail,
}: {
  title: string
  items: QueueEntry[]
  color: string
  renderDetail: (entry: QueueEntry) => React.ReactNode
}) {
  return (
    <div>
      <h3 className={`text-xs font-semibold uppercase tracking-wide ${color} px-4 py-2`}>
        {title} ({items.length})
      </h3>
      {items.length === 0 ? (
        <p className="text-2xs text-muted-foreground px-4 pb-2">No jobs in this state.</p>
      ) : (
        <div className="space-y-2 px-4">
          {items.map(entry => (
            <div key={entry.execution_id} className="min-w-0">
              <div className="flex items-start gap-3 p-2 rounded-lg border border-border/40 bg-muted/20 min-w-0 overflow-hidden">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{entry.title}</p>
                  <p className="text-2xs text-muted-foreground truncate">
                    {entry.current_step ? `Step: ${entry.current_step}` : entry.status}
                  </p>
                  <EntryLinks entry={entry} />
                </div>
              </div>
              {renderDetail(entry)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function ProcessingDrawer({ open, onOpenChange, reloadKey }: ProcessingDrawerProps) {
  const [snapshot, setSnapshot] = useState<QueueSnapshot>({ processing: [], queued: [], failed: [] })
  const [workflows, setWorkflows] = useState<Record<string, WorkflowProgress | null>>({})
  const loadedRef = useRef<Set<string>>(new Set())

  const loadSnapshot = useCallback(async () => {
    try {
      const data = await processingApi.queue()
      setSnapshot(data)
    } catch {
      // best effort
    }
  }, [])

  const loadWorkflow = useCallback(async (executionId: string) => {
    if (loadedRef.current.has(executionId)) return
    try {
      const detail = await processingApi.get(executionId)
      loadedRef.current.add(executionId)
      setWorkflows(prev => ({ ...prev, [executionId]: detail.workflow }))
    } catch {
      // best effort
    }
  }, [])

  useEffect(() => {
    if (!open) return
    loadSnapshot()
  }, [open, reloadKey, loadSnapshot])

  useEffect(() => {
    if (!open) return
    const allEntries = [...snapshot.processing, ...snapshot.queued, ...snapshot.failed]
    for (const entry of allEntries) {
      loadWorkflow(entry.execution_id)
    }
  }, [open, snapshot, loadWorkflow])

  useEffect(() => {
    if (!open) return

    return subscribeProcessingEvents((type, data) => {
      if (
        type === 'workflow.step.started' ||
        type === 'workflow.step.progress' ||
        type === 'workflow.step.completed' ||
        type === 'workflow.step.failed'
      ) {
        const incoming = data.payload.step
        if (!incoming) return
        if (loadedRef.current.has(data.execution_id)) {
          setWorkflows(prev => {
            const existing = prev[data.execution_id]
            if (!existing) return prev
            return { ...prev, [data.execution_id]: mergeWorkflowStep(existing, incoming) }
          })
        } else {
          loadWorkflow(data.execution_id)
        }
        return
      }

      if (type === 'queue.entry.removed') {
        loadedRef.current.delete(data.execution_id)
        setWorkflows(prev => {
          const { [data.execution_id]: _removed, ...rest } = prev
          return rest
        })
      }
      loadSnapshot()
    })
  }, [open, loadSnapshot, loadWorkflow])

  const renderDetail = useCallback((entry: QueueEntry) => {
    return <WorkflowPanel workflow={workflows[entry.execution_id] ?? null} entry={entry} />
  }, [workflows])

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold">Processing Queue</SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0 min-w-0">
          <div className="py-2 space-y-4 min-w-0">
            <QueueSection title="Running" items={snapshot.processing} color="text-emerald-500" renderDetail={renderDetail} />
            <QueueSection title="Waiting" items={snapshot.queued} color="text-blue-500" renderDetail={renderDetail} />
            <QueueSection title="Failed" items={snapshot.failed} color="text-red-500" renderDetail={renderDetail} />
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
