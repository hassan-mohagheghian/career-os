import { useState, useEffect, useCallback, useRef } from 'react'
import type { HistoryItemData } from '@/shared/lib/sourceConfig'
import { API_BASE, LOCAL_HISTORY_POLL_INTERVAL } from '@/shared/config/constants'

const API = API_BASE

interface UseLocalHistoryOptions {
  context: 'job' | 'company' | 'skill'
  job_num?: number
  company_id?: number
  skill_name?: string
  enabled?: boolean
}

interface UseLocalHistoryReturn {
  items: HistoryItemData[]
  loading: boolean
  activeCount: number
  singleRunning: HistoryItemData | null
  refresh: () => void
}

export function useLocalHistory(options: UseLocalHistoryOptions): UseLocalHistoryReturn {
  const { context, job_num, company_id, skill_name, enabled = true } = options

  const [items, setItems] = useState<HistoryItemData[]>([])
  const [loading, setLoading] = useState(false)
  const [activeCount, setActiveCount] = useState(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  // Build query string
  const buildUrl = useCallback(() => {
    const params = new URLSearchParams({ context })
    if (context === 'job' && job_num != null) params.set('job_num', String(job_num))
    if (context === 'company' && company_id != null) params.set('company_id', String(company_id))
    if (context === 'skill' && skill_name != null) params.set('skill_name', skill_name)
    return `${API}/local-history?${params.toString()}`
  }, [context, job_num, company_id, skill_name])

  const buildActiveUrl = useCallback(() => {
    const params = new URLSearchParams({ context })
    if (context === 'job' && job_num != null) params.set('job_num', String(job_num))
    if (context === 'company' && company_id != null) params.set('company_id', String(company_id))
    if (context === 'skill' && skill_name != null) params.set('skill_name', skill_name)
    return `${API}/local-history/active?${params.toString()}`
  }, [context, job_num, company_id, skill_name])

  const fetchHistory = useCallback(() => {
    if (!enabled) return
    setLoading(true)
    fetch(buildUrl())
      .then(r => r.ok ? r.json() : { items: [], total: 0 })
      .then(d => {
        if (mountedRef.current) setItems(d.items || [])
      })
      .catch(() => { if (mountedRef.current) setItems([]) })
      .finally(() => { if (mountedRef.current) setLoading(false) })
  }, [enabled, buildUrl])

  const fetchActiveCount = useCallback(() => {
    if (!enabled) return
    fetch(buildActiveUrl())
      .then(r => r.ok ? r.json() : { active_count: 0 })
      .then(d => {
        if (mountedRef.current) setActiveCount(d.active_count || 0)
      })
      .catch(() => { if (mountedRef.current) setActiveCount(0) })
  }, [enabled, buildActiveUrl])

  const refresh = useCallback(() => {
    fetchHistory()
    fetchActiveCount()
  }, [fetchHistory, fetchActiveCount])

  // Initial fetch
  useEffect(() => {
    mountedRef.current = true
    if (enabled) {
      fetchHistory()
      fetchActiveCount()
    }
    return () => { mountedRef.current = false }
  }, [enabled, fetchHistory, fetchActiveCount])

  // Polling when items are active
  useEffect(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    if (activeCount > 0) {
      pollRef.current = setInterval(() => {
        fetchHistory()
        fetchActiveCount()
      }, LOCAL_HISTORY_POLL_INTERVAL)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [activeCount, fetchHistory, fetchActiveCount])

  const singleRunning = activeCount === 1
    ? items.find(i => i.status === 'processing' || i.status === 'running' || i.status === 'queued') || null
    : null

  return { items, loading, activeCount, singleRunning, refresh }
}
