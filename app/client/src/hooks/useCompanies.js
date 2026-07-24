import { useState, useEffect, useCallback, useRef } from 'react'
import { useSocketIO, cancelJob, resetJob, watchCompany, unwatchCompany } from './useSocketIO'

const API = '/api'

export function useCompanies() {
  const [companies, setCompanies] = useState([])
  const [pendingCompanies, setPendingCompanies] = useState([])
  const socket = useSocketIO()
  const watchedRef = useRef(new Set())

  // Watch/unwatch rooms when pending companies list changes
  const syncWatchRooms = useCallback((list) => {
    const newIds = new Set(list.map(p => p.id))
    for (const id of watchedRef.current) {
      if (!newIds.has(id)) {
        unwatchCompany(id)
        watchedRef.current.delete(id)
      }
    }
    for (const id of newIds) {
      if (!watchedRef.current.has(id)) {
        watchCompany(id)
        watchedRef.current.add(id)
      }
    }
  }, [])

  // Unwatch all on unmount
  useEffect(() => {
    return () => {
      for (const id of watchedRef.current) {
        unwatchCompany(id)
      }
      watchedRef.current.clear()
    }
  }, [])

  const fetchCompanies = useCallback(() => {
    return fetch(`${API}/companies`).then(r => r.json()).then(setCompanies)
  }, [])

  const fetchPendingCompanies = useCallback(() => {
    return fetch(`${API}/pending-companies`).then(r => r.json()).then(list => {
      setPendingCompanies(list)
      syncWatchRooms(list)
      return list
    })
  }, [syncWatchRooms])

  const deleteCompany = useCallback(async (id) => {
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    fetchCompanies()
  }, [fetchCompanies])

  const reprocessCompany = useCallback(async (id) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    fetchCompanies()
  }, [fetchCompanies])

  const cancelPendingCompany = useCallback((id) => {
    cancelJob(id, 'pending_companies')
    fetchPendingCompanies()
  }, [fetchPendingCompanies])

  const resetPendingCompany = useCallback((id) => {
    resetJob(id, 'pending_companies')
    fetchPendingCompanies()
  }, [fetchPendingCompanies])

  const refresh = useCallback(() => {
    fetchCompanies()
    fetchPendingCompanies()
  }, [fetchCompanies, fetchPendingCompanies])

  // SocketIO real-time updates
  useEffect(() => {
    const handleUpdate = (data) => {
      setPendingCompanies(prev => prev.map(p => {
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
      setPendingCompanies(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const logs = Array.isArray(p.workflow_log) ? p.workflow_log : JSON.parse(p.workflow_log || '[]')
        return { ...p, workflow_log: [...logs, { step: data.step, msg: data.msg, ts: data.ts }] }
      }))
    }
    const handleComplete = (data) => {
      setPendingCompanies(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'done', ...data } : p
      ))
      fetchCompanies()
    }
    const handleError = (data) => {
      setPendingCompanies(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'failed', error: data.msg } : p
      ))
    }

    socket.on('company:update', handleUpdate)
    socket.on('company:log', handleLog)
    socket.on('company:complete', handleComplete)
    socket.on('company:error', handleError)

    // Initial fetch
    fetchCompanies()
    fetchPendingCompanies()

    return () => {
      socket.off('company:update', handleUpdate)
      socket.off('company:log', handleLog)
      socket.off('company:complete', handleComplete)
      socket.off('company:error', handleError)
    }
  }, [socket, fetchCompanies, fetchPendingCompanies])

  return {
    companies, setCompanies, pendingCompanies,
    fetchCompanies, fetchPendingCompanies,
    deleteCompany, reprocessCompany, cancelPendingCompany, resetPendingCompany, refresh
  }
}
