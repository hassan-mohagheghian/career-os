import { useState, useCallback, useEffect } from 'react'
import { useSocketIO, watchCareerIntel, unwatchCareerIntel } from './useSocketIO'

const API = '/api'

export function useCareerIntel() {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState({})
  const [progress, setProgress] = useState({ running: false })
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshing, setRefreshing] = useState({})
  const [error, setError] = useState(null)
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

  // Initial load + WebSocket for real-time updates
  useEffect(() => {
    fetchData()
    fetchStatus()
    fetchProgress()
  }, [fetchData, fetchStatus, fetchProgress])

  useEffect(() => {
    if (!socket) return

    const handleProgress = (data) => {
      setProgress(data)
      // When analysis completes/fails/cancels, refresh all data
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

  const refreshSection = useCallback(async (section) => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/${section}/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      // Optimistically show progress bar immediately (WebSocket will update with real data)
      setProgress(p => ({ ...p, running: true, type: section }))
      setRefreshing(r => ({ ...r, [section]: true }))
      return true
    } catch (e) {
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
      // Optimistically show progress bar immediately (WebSocket will update with real data)
      setProgress(p => ({ ...p, running: true, type: 'all' }))
      setRefreshing(r => ({ ...r, all: true }))
      return true
    } catch (e) {
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
    } catch (e) {
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
