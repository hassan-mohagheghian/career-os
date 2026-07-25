import { useState, useCallback, useEffect } from 'react'
import { useSocketIO, watchCareerIntel, unwatchCareerIntel } from './useSocketIO'

const API = '/api'

interface ProgressData {
  running: boolean
  type?: string
  status?: string
  session_id?: string
  section?: string
  message?: string
  error?: string
  run_id?: number
  started_at?: string
  [key: string]: any
}

interface SectionStatus {
  status: string
  lastRun: string | null
  completedAt?: string
  error?: string
}

export function useCareerIntel() {
  const [data, setData] = useState<Record<string, any> | null>(null)
  const [status, setStatus] = useState<Record<string, SectionStatus>>({})
  const [progress, setProgress] = useState<ProgressData>({ running: false })
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshing, setRefreshing] = useState<Record<string, boolean>>({})
  const [error, setError] = useState<string | null>(null)
  const socket = useSocketIO()

  const fetchData = useCallback(() => {
    return fetch(`${API}/career-intelligence`)
      .then(r => r.ok ? r.json() : {})
      .then(d => setData(d))
      .catch(() => setData({}))
  }, [])

  const fetchStatus = useCallback(() => {
    return fetch(`${API}/career-intelligence/status`)
      .then(r => r.ok ? r.json() : {})
      .then(d => setStatus(d))
      .catch(() => setStatus({}))
  }, [])

  const fetchProgress = useCallback(() => {
    return fetch(`${API}/career-intelligence/progress`)
      .then(r => r.ok ? r.json() : { running: false })
      .then(d => setProgress(d))
      .catch(() => setProgress({ running: false }))
  }, [])

  useEffect(() => {
    fetchData()
    fetchStatus()
    fetchProgress()
  }, [fetchData, fetchStatus, fetchProgress])

  useEffect(() => {
    if (!socket) return

    const handleProgress = (data: ProgressData) => {
      setProgress(prev => ({ ...prev, ...data }))
      if (!data.running) {
        setRefreshing({})
        fetchStatus()
        fetchData()
      }
    }

    socket.on('career_intel:progress', handleProgress)
    watchCareerIntel()

    return () => {
      socket.off('career_intel:progress', handleProgress)
      unwatchCareerIntel()
    }
  }, [socket, fetchStatus, fetchData])

  const refreshSection = useCallback(async (section: string) => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/${section}/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      setProgress(p => ({ ...p, running: true, type: section }))
      setRefreshing(r => ({ ...r, [section]: true }))
      return true
    } catch {
      setError('Failed to start analysis')
      return false
    }
  }, [])

  const refreshAll = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      setProgress(p => ({ ...p, running: true, type: 'all' }))
      setRefreshing(r => ({ ...r, all: true }))
      return true
    } catch {
      setError('Failed to start analysis')
      return false
    }
  }, [])

  const cancelRun = useCallback(async () => {
    try {
      const res = await fetch(`${API}/career-intelligence/cancel`, { method: 'POST' })
      const body = await res.json()
      if (body.status === 'cancelled') {
        setRefreshing({})
        fetchProgress()
        fetchStatus()
        fetchData()
        return true
      }
    } catch {
      setError('Failed to cancel analysis')
    }
    return false
  }, [fetchData, fetchStatus, fetchProgress])

  return {
    data, setData,
    status, progress,
    activeTab, setActiveTab, refreshing,
    error, setError,
    fetchData, fetchStatus, fetchProgress,
    refreshSection, refreshAll, cancelRun
  }
}
