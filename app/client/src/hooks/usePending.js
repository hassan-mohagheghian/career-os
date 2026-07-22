import { useState, useEffect, useRef, useCallback } from 'react'

const API = '/api'

export function usePending(onJobDone) {
  const [pending, setPending] = useState([])
  const [urlInput, setUrlInput] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [processImmediately, setProcessImmediately] = useState(true)
  const [urlError, setUrlError] = useState('')
  const [duplicateJob, setDuplicateJob] = useState(null)
  const seenDoneRef = useRef(new Set())

  const fetchPending = useCallback(() => {
    return fetch(`${API}/pending`).then(r => r.json()).then(list => {
      setPending(list)
      return list
    })
  }, [])

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
    await fetch(`${API}/pending/${id}/reset`, { method: 'PUT' })
    fetchPending()
  }, [fetchPending])

  const pausePending = useCallback(async (id) => {
    await fetch(`${API}/pending/${id}/pause`, { method: 'PUT' })
    fetchPending()
  }, [fetchPending])

  useEffect(() => {
    let es
    const checkDone = (pendingList) => {
      const newlyDone = pendingList.filter(p => p.status === 'done' && !seenDoneRef.current.has(p.id))
      if (newlyDone.length > 0) {
        newlyDone.forEach(p => seenDoneRef.current.add(p.id))
        onJobDone?.()
      }
    }
    const connect = () => {
      es = new EventSource(`${API}/pending/stream`)
      es.onmessage = (e) => {
        try {
          const list = JSON.parse(e.data)
          setPending(list)
          checkDone(list)
        } catch {}
      }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    const poll = setInterval(() => { fetchPending().then(checkDone) }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [fetchPending, onJobDone])

  return {
    pending, urlInput, setUrlInput, urlError, setUrlError,
    submitting, processImmediately, setProcessImmediately,
    duplicateJob, setDuplicateJob,
    fetchPending, submitUrl, deletePending, processPending, resetPending, pausePending
  }
}
