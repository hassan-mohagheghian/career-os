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
  const [dashboardData, setDashboardData] = useState<any>(null)
  const socket = useSocketIO()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(() => {
    return fetch(`${API}/insights/skills-intel`)
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

  const fetchDashboard = useCallback(() => {
    return fetch(`${API}/skills-intelligence/dashboard`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setDashboardData(d); })
      .catch(() => {})
  }, [])

  const fetchStatus = useCallback(() => {
    return fetch(`${API}/insights/status`)
      .then(r => r.ok ? r.json() : {})
      .then(d => setStatus(d))
      .catch(() => setStatus({}))
  }, [])

  const fetchProgress = useCallback(() => {
    return fetch(`${API}/insights/progress`)
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
    fetchDashboard()
    pollActiveSkillJobs()
  }, [fetchData, fetchStatus, fetchProgress, fetchSkillProgress, fetchDashboard, pollActiveSkillJobs])

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
        fetchDashboard()
      }
    }

    const handleSkillUpdate = (evt: any) => {
      const { skill, job_id, status: jobStatus, ...rest } = evt
      if (!skill) return

      setSkillGenJobs(prev => {
        const idx = prev.findIndex((j: any) => j.skill_name === skill || j.job_id === job_id)
        const merged = {
          skill_name: skill,
          job_id,
          ...rest,
          status: jobStatus,
        }

        if (jobStatus === 'completed' || jobStatus === 'cancelled') {
          return idx >= 0 ? [...prev.slice(0, idx), ...prev.slice(idx + 1)] : prev
        }

        if (idx >= 0) {
          const next = [...prev]
          next[idx] = { ...next[idx], ...merged }
          return next
        }
        return [...prev, merged]
      })

      fetchSkillProgress()
      if (jobStatus === 'completed' || jobStatus === 'failed' || jobStatus === 'cancelled') {
        pollActiveSkillJobs()
      }
    }

    socket.on('insights:progress', handleProgress)
    socket.on('skill_roadmap:update', handleSkillUpdate)
    watchSkills()

    return () => {
      socket.off('insights:progress', handleProgress)
      socket.off('skill_roadmap:update', handleSkillUpdate)
      unwatchSkills()
    }
  }, [socket, fetchStatus, fetchData, fetchSkillProgress, pollActiveSkillJobs])

  // Poll active skill jobs — always if there are active jobs, or during insights generation
  useEffect(() => {
    const shouldPoll = (progress.running && progress.type === 'skills_intel') || skillGenJobs.some((j: any) => j.status === 'running' || j.status === 'queued')
    if (shouldPoll) {
      pollRef.current = setInterval(pollActiveSkillJobs, 3000)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [progress.running, progress.type, skillGenJobs, pollActiveSkillJobs])

  const refresh = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(`${API}/insights/skills-intel/refresh`, { method: 'POST' })
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
      const res = await fetch(`${API}/insights/cancel`, { method: 'POST' })
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
    dashboardData,
    refresh, cancelRun, fetchProgress,
    refreshSkillRoadmapProgress: fetchSkillProgress,
    refreshDashboard: fetchDashboard,
  }
}
