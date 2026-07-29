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
  const [skills, setSkills] = useState<any[]>([])
  const [skillRoadmapProgress, setSkillRoadmapProgress] = useState<Record<string, any>>({})
  const [skillGenJobs, setSkillGenJobs] = useState<any[]>([])
  const [dashboardData, setDashboardData] = useState<any>(null)
  const socket = useSocketIO()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(() => {
    return Promise.resolve(null)
  }, [])

  const fetchSkills = useCallback(() => {
    return fetch(`${API}/skills`)
      .then(r => r.ok ? r.json() : [])
      .then(d => { if (Array.isArray(d)) setSkills(d); })
      .catch(() => {})
  }, [])

  const fetchDashboard = useCallback(() => {
    return fetch(`${API}/skills-intelligence/dashboard`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setDashboardData(d); })
      .catch(() => {})
  }, [])

  const fetchStatus = useCallback(() => {
    return Promise.resolve({})
  }, [])

  const fetchProgress = useCallback(() => {
    return Promise.resolve({ running: false })
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
    fetchSkills()
    fetchSkillProgress()
    fetchDashboard()
    pollActiveSkillJobs()
  }, [fetchData, fetchStatus, fetchProgress, fetchSkills, fetchSkillProgress, fetchDashboard, pollActiveSkillJobs])

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

    socket.on('skill_roadmap:update', handleSkillUpdate)
    watchSkills()

    return () => {
      socket.off('skill_roadmap:update', handleSkillUpdate)
      unwatchSkills()
    }
  }, [socket, fetchStatus, fetchData, fetchSkillProgress, pollActiveSkillJobs])

  // Poll active skill jobs — always if there are active jobs
  useEffect(() => {
    const shouldPoll = skillGenJobs.some((j: any) => j.status === 'running' || j.status === 'queued')
    if (shouldPoll) {
      pollRef.current = setInterval(pollActiveSkillJobs, 3000)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [progress.running, progress.type, skillGenJobs, pollActiveSkillJobs])

  const refresh = useCallback(async () => {
    return false
  }, [])

  const cancelRun = useCallback(async () => {
    return false
  }, [])

  return {
    data, status, progress, refreshing, error,
    skills, skillRoadmapProgress, skillGenJobs,
    dashboardData,
    refresh, cancelRun, fetchProgress,
    refreshSkillRoadmapProgress: fetchSkillProgress,
    refreshDashboard: fetchDashboard,
  }
}
