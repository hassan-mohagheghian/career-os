import { useState, useCallback, useEffect, useRef } from 'react'
import { useSocketIO, watchSkills, unwatchSkills } from '@/shared/hooks/useSocketIO'

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

export function useSkills() {
  const [data, setData] = useState<Record<string, any> | null>(null)
  const [status, setStatus] = useState<Record<string, SectionStatus>>({})
  const [progress, setProgress] = useState<ProgressData>({ running: false })
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skillRoadmapProgress, setSkillRoadmapProgress] = useState<Record<string, any>>({})
  const [skillGenJobs, setSkillGenJobs] = useState<any[]>([])
  const socket = useSocketIO()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(() => {
    return fetch(`${API}/career-intelligence/skills-intel`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d && d.data) {
          setData({ skills_intel: d.data })
        } else if (d) {
          setData({ skills_intel: d })
        } else {
          setData(null)
        }
      })
      .catch(() => setData(null))
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

  const fetchSkillProgress = useCallback(() => {
    return fetch(`${API}/skill-roadmap-progress/all`)
      .then(r => r.ok ? r.json() : {})
      .then(d => setSkillRoadmapProgress(d))
      .catch(() => setSkillRoadmapProgress({}))
  }, [])

  const pollActiveSkillJobs = useCallback(() => {
    fetch(`${API}/skill-roadmap-jobs?limit=10`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => {
        const active = (d.items || []).filter((j: any) =>
          j.status === 'running' || j.status === 'queued' || j.status === 'failed'
        )
        setSkillGenJobs(active)
      })
      .catch(() => setSkillGenJobs([]))
  }, [])

  // Initial load
  useEffect(() => {
    fetchData()
    fetchStatus()
    fetchProgress()
    fetchSkillProgress()
  }, [fetchData, fetchStatus, fetchProgress, fetchSkillProgress])

  // SocketIO for real-time updates
  useEffect(() => {
    if (!socket) return

    const handleProgress = (data: any) => {
      setProgress(prev => ({ ...prev, ...data }))
      if (!data.running) {
        setRefreshing(false)
        fetchStatus()
        fetchData()
        fetchSkillProgress()
      }
    }

    const handleSkillUpdate = () => {
      fetchSkillProgress()
      pollActiveSkillJobs()
    }

    socket.on('career_intel:progress', handleProgress)
    socket.on('skill_roadmap:update', handleSkillUpdate)
    watchSkills()

    return () => {
      socket.off('career_intel:progress', handleProgress)
      socket.off('skill_roadmap:update', handleSkillUpdate)
      unwatchSkills()
    }
  }, [socket, fetchStatus, fetchData, fetchSkillProgress, pollActiveSkillJobs])

  // Poll active skill jobs when generation is running
  useEffect(() => {
    if (progress.running && progress.type === 'skills_intel') {
      pollRef.current = setInterval(pollActiveSkillJobs, 3000)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [progress.running, progress.type, pollActiveSkillJobs])

  const refresh = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(`${API}/career-intelligence/skills-intel/refresh`, { method: 'POST' })
      const body = await res.json()
      if (res.status === 409) {
        setError(body.message || 'Analysis already in progress')
        return false
      }
      setProgress(p => ({ ...p, running: true, type: 'skills_intel' }))
      setRefreshing(true)
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
        setRefreshing(false)
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
    data, status, progress, refreshing, error,
    skillRoadmapProgress, skillGenJobs,
    refresh, cancelRun, fetchProgress,
    refreshSkillRoadmapProgress: fetchSkillProgress,
  }
}
