import { useState, useEffect, useRef, useCallback } from 'react'
import { useSocketIO, cancelJob, resetJob } from './useSocketIO'

const API = '/api'

interface PendingJob {
  num: number
  url: string
  status: string
  company: string | null
  job_num: number | null
  workflow_log: any
  session_id: string | null
  error: string | null
  [key: string]: any
}

export function usePending(onJobDone?: () => void) {
  const [pending, setPending] = useState<PendingJob[]>([])
  const [urlInput, setUrlInput] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [processImmediately, setProcessImmediately] = useState(true)
  const [urlError, setUrlError] = useState('')
  const [duplicateJob, setDuplicateJob] = useState<any>(null)
  const seenDoneRef = useRef(new Set<number>())
  const onJobDoneRef = useRef(onJobDone)
  onJobDoneRef.current = onJobDone
  const socket = useSocketIO()

  const fetchPending = useCallback(() => {
    return fetch(`${API}/pending`).then(r => r.json()).then((list: PendingJob[]) => {
      setPending(list)
      return list
    })
  }, [])

  const processPending = useCallback(async (id: number) => {
    await fetch(`${API}/pending/${id}/process`, { method: 'POST' })
    fetchPending()
  }, [fetchPending])

  const submitUrl = useCallback(async (extraNotes?: Array<{ type: string; content: string }>, extraLinks?: Array<{ url: string; title: string }>) => {
    if (!urlInput.trim()) return
    setUrlError('')
    setSubmitting(true)
    try {
      const payload: Record<string, any> = { url: urlInput.trim(), source: 'web' }
      if (extraNotes && extraNotes.length > 0) payload.notes = extraNotes
      if (extraLinks && extraLinks.length > 0) payload.links = extraLinks
      const res = await fetch(`${API}/pending`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (res.ok && data.status === 'exists') {
        setDuplicateJob(data)
        setUrlInput('')
        return
      }
      if (!res.ok) {
        setUrlError(data.error || 'Failed to add URL')
        return
      }
      setUrlInput('')
      fetchPending()
      if (processImmediately && data.num) await processPending(data.num)
    } finally {
      setSubmitting(false)
    }
  }, [urlInput, processImmediately, fetchPending, processPending])

  const deletePending = useCallback(async (id: number) => {
    await fetch(`${API}/pending/${id}`, { method: 'DELETE' })
    fetchPending()
  }, [fetchPending])

  const resetPending = useCallback(async (id: number) => {
    resetJob(id, 'pending_jobs')
    fetchPending()
  }, [fetchPending])

  const pausePending = useCallback(async (id: number) => {
    cancelJob(id, 'pending_jobs')
    fetchPending()
  }, [fetchPending])

  useEffect(() => {
    const handleUpdate = (data: any) => {
      setPending(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const updated = { ...p, ...data }
        if (data.step && data.step !== 'session_id') {
          updated[data.step] = data.val
        }
        return updated
      }))
    }
    const handleLog = (data: any) => {
      setPending(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const logs = Array.isArray(p.workflow_log) ? p.workflow_log : JSON.parse(p.workflow_log || '[]')
        return { ...p, workflow_log: [...logs, { step: data.step, msg: data.msg, ts: data.ts }] }
      }))
    }
    const handleComplete = (data: any) => {
      setPending(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'completed', ...data } : p
      ))
      if (!seenDoneRef.current.has(data.id)) {
        seenDoneRef.current.add(data.id)
        onJobDoneRef.current?.()
      }
    }
    const handleError = (data: any) => {
      setPending(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'failed', error: data.msg } : p
      ))
    }
    const handleProgress = (data: any) => {
      setPending(prev => prev.map(p => {
        if (p.id !== data.id) return p
        return {
          ...p,
          status: data.status || p.status,
          current_node: data.current_node,
          progress_pct: data.progress_pct,
          progress_msg: data.message,
        }
      }))
    }

    socket.on('pending:update', handleUpdate)
    socket.on('pending:log', handleLog)
    socket.on('pending:complete', handleComplete)
    socket.on('pending:error', handleError)
    socket.on('pending:progress', handleProgress)

    fetchPending()

    return () => {
      socket.off('pending:update', handleUpdate)
      socket.off('pending:log', handleLog)
      socket.off('pending:complete', handleComplete)
      socket.off('pending:error', handleError)
      socket.off('pending:progress', handleProgress)
    }
  }, [socket, fetchPending])

  return {
    pending, urlInput, setUrlInput, urlError, setUrlError,
    submitting, processImmediately, setProcessImmediately,
    duplicateJob, setDuplicateJob,
    fetchPending, submitUrl, deletePending, processPending, resetPending, pausePending
  }
}
