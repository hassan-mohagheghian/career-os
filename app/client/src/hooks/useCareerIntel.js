import { useState, useCallback, useRef, useEffect } from 'react'

const API = '/api'

export function useCareerIntel() {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState({})
  const [progress, setProgress] = useState({ running: false })
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshing, setRefreshing] = useState({})
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

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

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      await fetchProgress()
      await fetchStatus()
      await fetchData()
    }, 2000)
  }, [fetchProgress, fetchStatus, fetchData, stopPolling])

  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  const refreshSection = useCallback(async (section) => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/${section}/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      setRefreshing(r => ({ ...r, [section]: true }))
      startPolling()
      // Wait for completion
      let attempts = 0
      const wait = async () => {
        await new Promise(res => setTimeout(res, 2000))
        const p = await fetch(`${API}/career-intelligence/progress`).then(r => r.json()).catch(() => ({ running: false }))
        if (p.running && attempts < 60) {
          attempts++
          wait()
        } else {
          stopPolling()
          setRefreshing(r => ({ ...r, [section]: false }))
          await fetchProgress()
          await fetchStatus()
          await fetchData()
        }
      }
      wait()
      return true
    } catch (e) {
      setError('Failed to start analysis')
      return false
    }
  }, [fetchData, fetchStatus, fetchProgress, startPolling, stopPolling])

  const refreshAll = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      setRefreshing(r => ({ ...r, all: true }))
      startPolling()
      let attempts = 0
      const wait = async () => {
        await new Promise(res => setTimeout(res, 3000))
        const p = await fetch(`${API}/career-intelligence/progress`).then(r => r.json()).catch(() => ({ running: false }))
        if (p.running && attempts < 60) {
          attempts++
          wait()
        } else {
          stopPolling()
          setRefreshing(r => ({ ...r, all: false }))
          await fetchProgress()
          await fetchStatus()
          await fetchData()
        }
      }
      wait()
      return true
    } catch (e) {
      setError('Failed to start analysis')
      return false
    }
  }, [fetchData, fetchStatus, fetchProgress, startPolling, stopPolling])

  const cancelRun = useCallback(async () => {
    try {
      const res = await fetch(`${API}/career-intelligence/cancel`, { method: 'POST' })
      const body = await res.json()
      if (body.status === 'cancelled') {
        stopPolling()
        setRefreshing({})
        await fetchProgress()
        await fetchStatus()
        await fetchData()
        return true
      }
    } catch (e) {
      setError('Failed to cancel analysis')
    }
    return false
  }, [fetchData, fetchStatus, fetchProgress, stopPolling])

  return {
    data, setData,
    status, progress,
    activeTab, setActiveTab, refreshing,
    error, setError,
    fetchData, fetchStatus, fetchProgress,
    refreshSection, refreshAll, cancelRun
  }
}
