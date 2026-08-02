import { useState, useRef, useCallback } from 'react'
import { WORKFLOW_WS_PORT } from '@/shared/config/constants'

interface WorkflowLog {
  step: string
  msg: string
  ts?: string
}

interface WorkflowItem {
  id: number
  [key: string]: any
}

export function useWorkflow() {
  const [workflowDrawer, setWorkflowDrawer] = useState<WorkflowItem | null>(null)
  const [workflowLogs, setWorkflowLogs] = useState<WorkflowLog[]>([])
  const workflowWs = useRef<WebSocket | null>(null)
  const workflowEndRef = useRef<HTMLDivElement | null>(null)

  const connectWorkflowWs = useCallback((pid: number) => {
    if (workflowWs.current) workflowWs.current.close()
    const ws = new WebSocket(`ws://${window.location.hostname}:${WORKFLOW_WS_PORT}`)
    workflowWs.current = ws
    ws.onopen = () => { ws.send(JSON.stringify({ action: 'watch', pid })) }
    ws.onmessage = (e: MessageEvent) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt.type === 'state') {
          setWorkflowLogs(evt.logs || [])
        } else if (evt.type === 'tool_output') {
          const { stream, data } = evt
          if (stream === 'input') setWorkflowLogs(prev => [...prev, { step: 'cmd', msg: data, ts: evt.ts }])
          else if (stream === 'output') data.split('\n').forEach((line: string) => { if (line.trim()) setWorkflowLogs(prev => [...prev, { step: 'out', msg: line, ts: evt.ts }]) })
          else if (stream === 'error') setWorkflowLogs(prev => [...prev, { step: 'err', msg: data, ts: evt.ts }])
          else if (stream === 'text') setWorkflowLogs(prev => [...prev, { step: 'ai', msg: data, ts: evt.ts }])
        } else if (evt.type === 'provider_event' && evt.event?.type === 'step_finish') {
          const reason = evt.event.part?.reason || ''
          const tokens = evt.event.part?.tokens?.total || 0
          setWorkflowLogs(prev => [...prev, { step: 'step', msg: `Step finished: ${reason} (${tokens} tokens)`, ts: evt.ts }])
        } else if (evt.type === 'provider_raw') {
          setWorkflowLogs(prev => [...prev, { step: 'raw', msg: evt.line, ts: evt.ts }])
        } else if (evt.type === 'job_info') {
          // handled by parent
        } else if (evt.type === 'step') {
          setWorkflowLogs(prev => [...prev, { step: evt.step, msg: `[${evt.status}]`, ts: evt.ts }])
        } else if (evt.type === 'complete') {
          setWorkflowLogs(prev => [...prev, { step: 'done', msg: `Complete: ${evt.company} #${evt.num}`, ts: evt.ts }])
        } else if (evt.type === 'error') {
          setWorkflowLogs(prev => [...prev, { step: 'error', msg: evt.msg, ts: evt.ts }])
        }
      } catch { /* ignore parse errors */ }
    }
  }, [])

  const openWorkflow = useCallback((item: WorkflowItem) => {
    setWorkflowLogs([])
    setWorkflowDrawer(item)
    connectWorkflowWs(item.id)
  }, [connectWorkflowWs])

  const closeWorkflow = useCallback(() => {
    workflowWs.current?.close()
    setWorkflowDrawer(null)
    setWorkflowLogs([])
  }, [])

  return {
    workflowDrawer, workflowLogs, workflowEndRef,
    openWorkflow, closeWorkflow
  }
}
