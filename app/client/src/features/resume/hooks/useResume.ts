import { useState, useCallback, useEffect, useRef } from 'react'
import { toast } from 'sonner'

const API = '/api'

export function useResume() {
  const [resumes, setResumes] = useState<any[]>([])
  const [linkedinProfiles, setLinkedinProfiles] = useState<any[]>([])
  const [generationProgress, setGenerationProgress] = useState<any>(null)
  const [generationId, setGenerationId] = useState<number | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const fetchResumes = useCallback(() => {
    return fetch(`${API}/resumes`).then(r => r.json()).then(setResumes)
  }, [])

  const fetchLinkedin = useCallback(() => {
    return fetch(`${API}/linkedin`).then(r => r.json()).then(setLinkedinProfiles)
  }, [])

  const generateResume = useCallback(async (num: number, setDrawer?: (fn: (prev: any) => any) => void) => {
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error || 'Failed'); return }
      setGenerationId(data.gen_id)
      setGenerationProgress({ running: true, status: 'queued', step: 0, total_steps: 5 })
    } catch {
      toast.error('Failed to start generation')
    }
  }, [])

  const generateCover = useCallback(async (num: number, setDrawer?: (fn: (prev: any) => any) => void) => {
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error || 'Failed'); return }
      setGenerationId(data.gen_id)
      setGenerationProgress({ running: true, status: 'queued', step: 0, total_steps: 5 })
    } catch {
      toast.error('Failed to start generation')
    }
  }, [])

  const cancelGeneration = useCallback(async () => {
    if (!generationId) return
    try {
      await fetch(`${API}/generations/${generationId}/cancel`, { method: 'POST' })
      setGenerationProgress(null)
      setGenerationId(null)
      toast.info('Generation cancelled')
    } catch {
      toast.error('Failed to cancel')
    }
  }, [generationId])

  // Poll for progress
  useEffect(() => {
    if (!generationId) {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/generations/${generationId}`)
        const data = await res.json()

        // Calculate step from progress
        const steps = ['step_prepare', 'step_context', 'step_generate', 'step_save', 'step_done']
        const completedSteps = steps.filter(s => data[s] === 1).length

        setGenerationProgress({
          running: data.status === 'processing' || data.status === 'queued',
          status: data.status,
          step: completedSteps,
          total_steps: 5,
          error: data.error,
          elapsed_seconds: data.created_at
            ? Math.floor((Date.now() - new Date(data.created_at).getTime()) / 1000)
            : 0,
        })

        if (data.status === 'done') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          setGenerationId(null)
          fetchResumes()
          toast.success('Generation complete!')
          setTimeout(() => setGenerationProgress(null), 2000)
        } else if (data.status === 'failed') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          setGenerationId(null)
          toast.error(data.error || 'Generation failed')
        } else if (data.status === 'cancelled') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          setGenerationId(null)
        }
      } catch {
        // Polling error — ignore, will retry
      }
    }, 2000)

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [generationId, fetchResumes])

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    generationProgress, generationId,
    fetchResumes, fetchLinkedin, generateResume, generateCover, cancelGeneration
  }
}
