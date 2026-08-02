import { useState, useEffect, useCallback, useRef } from 'react'
import { useSocketIO, watchSkills, unwatchSkills } from './useSocketIO'
import type { HistoryItemData } from '@/shared/lib/sourceConfig'

const API = '/api'

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
  const socket = useSocketIO()
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
      }, 3000)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [activeCount, fetchHistory, fetchActiveCount])

  // WebSocket subscriptions for real-time updates
  useEffect(() => {
    if (!socket || !enabled) return

    const handleUpdate = (data: any) => {
      // Optimistically update the item in the list
      setItems(prev => prev.map(item => {
        if (item.id !== data.id) return item
        const updated = { ...item }
        if (data.status) updated.status = data.status
        if (data.error) updated.error = data.error
        if (data.step !== undefined) (updated as any).step = data.step
        if (data.session_id) updated.session_id = data.session_id
        return updated
      }))
    }

    const handleComplete = (data: any) => {
      setItems(prev => prev.map(item => {
        if (item.id !== data.id) return item
        return { ...item, status: data.status || 'processed', completed_at: data.ts || new Date().toISOString() }
      }))
      // Re-fetch to get final state
      setTimeout(() => { fetchHistory(); fetchActiveCount() }, 500)
    }

    const handleError = (data: any) => {
      setItems(prev => prev.map(item => {
        if (item.id !== data.id) return item
        return { ...item, status: 'failed', error: data.msg || 'Failed' }
      }))
      setTimeout(() => { fetchHistory(); fetchActiveCount() }, 500)
    }

    const handleSkillUpdate = (data: any) => {
      if (context === 'skill' && data.skill === skill_name) {
        setItems(prev => prev.map(item => {
          if (item.id !== data.id) return item
          const updated = { ...item }
          if (data.status) updated.status = data.status
          if (data.step !== undefined) (updated as any).step = data.step
          return updated
        }))
        if (data.status === 'processed' || data.status === 'failed' || data.status === 'cancelled') {
          setTimeout(() => { fetchHistory(); fetchActiveCount() }, 500)
        }
      }
    }

    // Subscribe to relevant rooms
    if (context === 'job' && job_num != null) {
      // Listen to all pending updates (we filter client-side by job_num)
      socket.on('pending:update', handleUpdate)
      socket.on('pending:complete', handleComplete)
      socket.on('pending:error', handleError)
      socket.on('generation:update', handleUpdate)
      socket.on('generation:complete', handleComplete)
      socket.on('generation:error', handleError)
    } else if (context === 'company' && company_id != null) {
      socket.on('company:update', handleUpdate)
      socket.on('company:complete', handleComplete)
      socket.on('company:error', handleError)
    } else if (context === 'skill') {
      watchSkills()
      socket.on('skill_roadmap:update', handleSkillUpdate)
    }

    return () => {
      socket.off('pending:update', handleUpdate)
      socket.off('pending:complete', handleComplete)
      socket.off('pending:error', handleError)
      socket.off('generation:update', handleUpdate)
      socket.off('generation:complete', handleComplete)
      socket.off('generation:error', handleError)
      socket.off('company:update', handleUpdate)
      socket.off('company:complete', handleComplete)
      socket.off('company:error', handleError)
      socket.off('skill_roadmap:update', handleSkillUpdate)
      if (context === 'skill') unwatchSkills()
    }
  }, [socket, enabled, context, job_num, company_id, skill_name, fetchHistory, fetchActiveCount])

  const singleRunning = activeCount === 1
    ? items.find(i => i.status === 'processing' || i.status === 'running' || i.status === 'queued') || null
    : null

  return { items, loading, activeCount, singleRunning, refresh }
}
