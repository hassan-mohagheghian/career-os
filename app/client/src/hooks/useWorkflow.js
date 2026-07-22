import { useState, useRef, useCallback } from 'react'

export function useWorkflow() {
  const [workflowDrawer, setWorkflowDrawer] = useState(null)
  const [workflowLogs, setWorkflowLogs] = useState([])
  const workflowWs = useRef(null)
  const workflowEndRef = useRef(null)

  const connectWorkflowWs = useCallback((pid) => {
    if (workflowWs.current) workflowWs.current.close()
    const ws = new WebSocket(`ws://${window.location.hostname}:8765`)
    workflowWs.current = ws
    ws.onopen = () => { ws.send(JSON.stringify({ action: 'watch', pid })) }
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt.type === 'state') {
          setWorkflowLogs(evt.logs || [])
        } else if (evt.type === 'tool_output') {
          const { stream, data } = evt
          if (stream === 'input') setWorkflowLogs(prev => [...prev, { step: 'cmd', msg: data, ts: evt.ts }])
          else if (stream === 'output') data.split('\n').forEach(line => { if (line.trim()) setWorkflowLogs(prev => [...prev, { step: 'out', msg: line, ts: evt.ts }]) })
          else if (stream === 'error') setWorkflowLogs(prev => [...prev, { step: 'err', msg: data, ts: evt.ts }])
          else if (stream === 'text') setWorkflowLogs(prev => [...prev, { step: 'mimo', msg: data, ts: evt.ts }])
        } else if (evt.type === 'mimo_event' && evt.event?.type === 'step_finish') {
          const reason = evt.event.part?.reason || ''
          const tokens = evt.event.part?.tokens?.total || 0
          setWorkflowLogs(prev => [...prev, { step: 'step', msg: `Step finished: ${reason} (${tokens} tokens)`, ts: evt.ts }])
        } else if (evt.type === 'mimo_raw') {
          setWorkflowLogs(prev => [...prev, { step: 'raw', msg: evt.line, ts: evt.ts }])
        } else if (evt.type === 'job_info') {
          // This updates pending state - will be handled by parent
        } else if (evt.type === 'step') {
          setWorkflowLogs(prev => [...prev, { step: evt.step, msg: `[${evt.status}]`, ts: evt.ts }])
        } else if (evt.type === 'complete') {
          setWorkflowLogs(prev => [...prev, { step: 'done', msg: `Complete: ${evt.company} #${evt.num}`, ts: evt.ts }])
        } else if (evt.type === 'error') {
          setWorkflowLogs(prev => [...prev, { step: 'error', msg: evt.msg, ts: evt.ts }])
        }
      } catch {}
    }
  }, [])

  const openWorkflow = useCallback((item) => {
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
