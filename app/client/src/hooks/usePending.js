import { useState, useEffect, useRef, useCallback } from 'react'
import { useSocketIO, cancelJob, resetJob, watchPending, unwatchPending } from './useSocketIO'

const API = '/api'

export function usePending(onJobDone) {
  const [pending, setPending] = useState([])
  const [urlInput, setUrlInput] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [processImmediately, setProcessImmediately] = useState(true)
  const [urlError, setUrlError] = useState('')
  const [duplicateJob, setDuplicateJob] = useState(null)
  const seenDoneRef = useRef(new Set())
  const watchedRef = useRef(new Set())
  const socket = useSocketIO()

  // Watch/unwatch rooms when pending list changes
  const syncWatchRooms = useCallback((list) => {
    const newIds = new Set(list.map(p => p.id))
    // Unwatch removed jobs
    for (const id of watchedRef.current) {
      if (!newIds.has(id)) {
        unwatchPending(id)
        watchedRef.current.delete(id)
      }
    }
    // Watch new jobs
    for (const id of newIds) {
      if (!watchedRef.current.has(id)) {
        watchPending(id)
        watchedRef.current.add(id)
      }
    }
  }, [])

  // Unwatch all on unmount
  useEffect(() => {
    return () => {
      for (const id of watchedRef.current) {
        unwatchPending(id)
      }
      watchedRef.current.clear()
    }
  }, [])

  const fetchPending = useCallback(() => {
    return fetch(`${API}/pending`).then(r => r.json()).then(list => {
      setPending(list)
      syncWatchRooms(list)
      return list
    })
  }, [syncWatchRooms])

  const submitUrl = useCallback(async () => {
    if (!urlInput.trim()) return
    setUrlError('')
    setSubmitting(true)
    try {
      const res = await fetch(`${API}/pending`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput.trim(), source: 'web' })
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
      if (processImmediately && data.id) await processPending(data.id)
    } finally {
      setSubmitting(false)
    }
  }, [urlInput, processImmediately, fetchPending])

  const deletePending = useCallback(async (id) => {
    await fetch(`${API}/pending/${id}`, { method: 'DELETE' })
    fetchPending()
  }, [fetchPending])

  const processPending = useCallback(async (id) => {
    await fetch(`${API}/pending/${id}/process`, { method: 'POST' })
    fetchPending()
  }, [fetchPending])

  const resetPending = useCallback(async (id) => {
    resetJob(id, 'pending_jobs')
    fetchPending()
  }, [fetchPending])

  const cancelPending = useCallback(async (id) => {
    cancelJob(id, 'pending_jobs')
    fetchPending()
  }, [fetchPending])

  // SocketIO real-time updates
  useEffect(() => {
    const handleUpdate = (data) => {
      setPending(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const updated = { ...p, ...data }
        // Don't overwrite non-step fields like session_id with numeric val
        if (data.step && data.step !== 'session_id') {
          updated[data.step] = data.val
        }
        return updated
      }))
    }
    const handleLog = (data) => {
      setPending(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const logs = Array.isArray(p.workflow_log) ? p.workflow_log : JSON.parse(p.workflow_log || '[]')
        return { ...p, workflow_log: [...logs, { step: data.step, msg: data.msg, ts: data.ts }] }
      }))
    }
    const handleComplete = (data) => {
      setPending(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'done', ...data } : p
      ))
      if (!seenDoneRef.current.has(data.id)) {
        seenDoneRef.current.add(data.id)
        onJobDone?.()
      }
    }
    const handleError = (data) => {
      setPending(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'failed', error: data.msg } : p
      ))
    }

    socket.on('pending:update', handleUpdate)
    socket.on('pending:log', handleLog)
    socket.on('pending:complete', handleComplete)
    socket.on('pending:error', handleError)

    // Initial fetch
    fetchPending()

    return () => {
      socket.off('pending:update', handleUpdate)
      socket.off('pending:log', handleLog)
      socket.off('pending:complete', handleComplete)
      socket.off('pending:error', handleError)
    }
  }, [socket, fetchPending, onJobDone])

  return {
    pending, urlInput, setUrlInput, urlError, setUrlError,
    submitting, processImmediately, setProcessImmediately,
    duplicateJob, setDuplicateJob,
    fetchPending, submitUrl, deletePending, processPending, resetPending, cancelPending
  }
}
