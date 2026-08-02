import { useState, useCallback, useEffect } from 'react'
import { toast } from 'sonner'

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

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    activeGens, generationResult,
    fetchResumes, fetchLinkedin, generateResume, generateCover, cancelGeneration,
  }
}
