import { useState, useEffect, useCallback, useRef } from 'react'
import { useSocketIO, cancelJob, resetJob, watchCompany, unwatchCompany } from '@/shared/hooks/useSocketIO'

const API = '/api'

export function useCompanies() {
  const [companies, setCompanies] = useState<any[]>([])
  const socket = useSocketIO()
  const watchedRef = useRef(new Set<number>())

  const syncWatchRooms = useCallback((list: any[]) => {
    const newIds = new Set(list.map((p: any) => p.id))
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

  useEffect(() => {
    return () => {
      for (const id of watchedRef.current) {
        unwatchCompany(id)
      }
      watchedRef.current.clear()
    }
  }, [])

  const fetchCompanies = useCallback(() => {
    return fetch(`${API}/companies`).then(r => r.json()).then((list: any[]) => {
      setCompanies(list)
      syncWatchRooms(list)
      return list
    })
  }, [syncWatchRooms])

  const deleteCompany = useCallback(async (id: number) => {
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    fetchCompanies()
  }, [fetchCompanies])

  const reprocessCompany = useCallback(async (id: number) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    fetchCompanies()
  }, [fetchCompanies])

  const cancelCompanyAction = useCallback((id: number) => {
    cancelJob(id, 'company')
    fetchCompanies()
  }, [fetchCompanies])

  const resetCompanyAction = useCallback((id: number) => {
    resetJob(id, 'company')
    fetchCompanies()
  }, [fetchCompanies])

  const refresh = useCallback(() => {
    fetchCompanies()
  }, [fetchCompanies])

  useEffect(() => {
    const handleUpdate = (data: any) => {
      setCompanies(prev => prev.map(p => {
        if (p.id !== data.id) return p
        return { ...p, ...data }
      }))
    }
    const handleLog = (data: any) => {
      setCompanies(prev => prev.map(p => {
        if (p.id !== data.id) return p
        const logs = Array.isArray(p.workflow_log) ? p.workflow_log : JSON.parse(p.workflow_log || '[]')
        return { ...p, workflow_log: [...logs, { step: data.step, msg: data.msg, ts: data.ts }] }
      }))
    }
    const handleComplete = (data: any) => {
      setCompanies(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'completed', ...data } : p
      ))
    }
    const handleError = (data: any) => {
      setCompanies(prev => prev.map(p =>
        p.id === data.id ? { ...p, status: 'failed', error: data.msg } : p
      ))
    }
    const handleProgress = (data: any) => {
      setCompanies(prev => prev.map(p => {
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

    socket.on('company:update', handleUpdate)
    socket.on('company:log', handleLog)
    socket.on('company:complete', handleComplete)
    socket.on('company:error', handleError)
    socket.on('company:progress', handleProgress)

    fetchCompanies()

    return () => {
      socket.off('company:update', handleUpdate)
      socket.off('company:log', handleLog)
      socket.off('company:complete', handleComplete)
      socket.off('company:error', handleError)
      socket.off('company:progress', handleProgress)
    }
  }, [socket, fetchCompanies])

  return {
    companies, setCompanies,
    fetchCompanies,
    deleteCompany, reprocessCompany, cancelCompanyAction, resetCompanyAction, refresh
  }
}
