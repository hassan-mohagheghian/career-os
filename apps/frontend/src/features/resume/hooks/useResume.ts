import { useState, useCallback, useEffect } from 'react'
import { toast } from 'sonner'
import { useSocketIO, watchGeneration, unwatchGeneration } from '@/shared/hooks/useSocketIO'

const API = '/api'

interface ActiveGen {
  id: number
  type: string
  status: string
  step: number
  total_steps: number
  error?: string
}

export function useResume() {
  const [resumes, setResumes] = useState<any[]>([])
  const [linkedinProfiles, setLinkedinProfiles] = useState<any[]>([])
  const [activeGens, setActiveGens] = useState<Record<string, ActiveGen>>({})
  const [generationResult, setGenerationResult] = useState<any>(null)
  const socket = useSocketIO()

  const fetchResumes = useCallback(() => {
    return fetch(`${API}/resumes`).then(r => r.json()).then(setResumes)
  }, [])

  const fetchLinkedin = useCallback(() => {
    return fetch(`${API}/linkedin`).then(r => r.json()).then(setLinkedinProfiles)
  }, [])

  // Restore active generations on mount (survives page refresh)
  useEffect(() => {
    fetch(`${API}/resumes/active-generations`)
      .then(r => r.ok ? r.json() : [])
      .then((active: any[]) => {
        const map: Record<string, ActiveGen> = {}
        for (const gen of active) {
          const steps = ['step_prepare', 'step_context', 'step_generate', 'step_save', 'step_done']
          const completedSteps = steps.filter(s => gen[s] === 1).length
          map[gen.type] = {
            id: gen.id,
            type: gen.type,
            status: gen.status,
            step: completedSteps,
            total_steps: 5,
            error: gen.error,
          }
          watchGeneration(gen.id)
        }
        setActiveGens(map)
      })
      .catch(() => {})
  }, [])

  const generateResume = useCallback(async (num: number) => {
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error?.message || data.error || 'Failed'); return }
      setActiveGens(prev => ({
        ...prev,
        resume: { id: data.gen_id, type: 'resume', status: 'queued', step: 0, total_steps: 5 },
      }))
      watchGeneration(data.gen_id)
    } catch {
      toast.error('Failed to start generation')
    }
  }, [])

  const generateCover = useCallback(async (num: number) => {
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error?.message || data.error || 'Failed'); return }
      setActiveGens(prev => ({
        ...prev,
        cover: { id: data.gen_id, type: 'cover', status: 'queued', step: 0, total_steps: 5 },
      }))
      watchGeneration(data.gen_id)
    } catch {
      toast.error('Failed to start generation')
    }
  }, [])

  const cancelGeneration = useCallback(async (type?: string) => {
    const target = type || Object.keys(activeGens)[0]
    if (!target || !activeGens[target]) return
    const gen = activeGens[target]
    try {
      await fetch(`${API}/generations/${gen.id}/cancel`, { method: 'POST' })
      unwatchGeneration(gen.id)
      setActiveGens(prev => {
        const next = { ...prev }
        delete next[target]
        return next
      })
      toast.info(`${target === 'resume' ? 'Resume' : 'Cover letter'} generation cancelled`)
    } catch {
      toast.error('Failed to cancel')
    }
  }, [activeGens])

  // Listen for WebSocket generation events — handles ALL active generations
  useEffect(() => {
    if (!socket) return

    const handleUpdate = (data: any) => {
      setActiveGens(prev => {
        const entry = Object.values(prev).find(g => g.id === data.id)
        if (!entry) return prev
        const steps = ['step_prepare', 'step_context', 'step_generate', 'step_save', 'step_done']
        const completedSteps = steps.filter(s => data[s] === 1).length
        return {
          ...prev,
          [entry.type]: {
            ...entry,
            status: data.status,
            step: completedSteps,
            error: data.error,
          },
        }
      })
    }

    const handleComplete = (data: any) => {
      setActiveGens(prev => {
        const entry = Object.values(prev).find(g => g.id === data.id)
        if (!entry) return prev
        unwatchGeneration(entry.id)
        const next = { ...prev }
        delete next[entry.type]
        return next
      })
      setGenerationResult(data)
      fetchResumes()
      toast.success(`${data.type === 'resume' ? 'Resume' : 'Cover letter'} generated!`)
      setTimeout(() => setGenerationResult(null), 5000)
    }

    const handleError = (data: any) => {
      setActiveGens(prev => {
        const entry = Object.values(prev).find(g => g.id === data.id)
        if (!entry) return prev
        unwatchGeneration(entry.id)
        const next = { ...prev }
        delete next[entry.type]
        return next
      })
      toast.error(data.msg || 'Generation failed')
    }

    socket.on('generation:update', handleUpdate)
    socket.on('generation:complete', handleComplete)
    socket.on('generation:error', handleError)

    return () => {
      socket.off('generation:update', handleUpdate)
      socket.off('generation:complete', handleComplete)
      socket.off('generation:error', handleError)
    }
  }, [socket, fetchResumes])

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    activeGens, generationResult,
    fetchResumes, fetchLinkedin, generateResume, generateCover, cancelGeneration,
  }
}
