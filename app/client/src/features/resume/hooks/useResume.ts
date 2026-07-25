import { useState, useCallback, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import { useSocketIO, watchGeneration, unwatchGeneration } from '@/shared/hooks/useSocketIO'

const API = '/api'

export function useResume() {
  const [resumes, setResumes] = useState<any[]>([])
  const [linkedinProfiles, setLinkedinProfiles] = useState<any[]>([])
  const [generationProgress, setGenerationProgress] = useState<any>(null)
  const [generationId, setGenerationId] = useState<number | null>(null)
  const [generationType, setGenerationType] = useState<string | null>(null)
  const [generationResult, setGenerationResult] = useState<any>(null)
  const socket = useSocketIO()

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
      setGenerationType('resume')
      setGenerationProgress({ running: true, status: 'queued', step: 0, total_steps: 5, type: 'resume' })
      watchGeneration(data.gen_id)
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
      setGenerationType('cover')
      setGenerationProgress({ running: true, status: 'queued', step: 0, total_steps: 5, type: 'cover' })
      watchGeneration(data.gen_id)
    } catch {
      toast.error('Failed to start generation')
    }
  }, [])

  const cancelGeneration = useCallback(async () => {
    if (!generationId) return
    try {
      await fetch(`${API}/generations/${generationId}/cancel`, { method: 'POST' })
      unwatchGeneration(generationId)
      setGenerationProgress(null)
      setGenerationId(null)
      setGenerationType(null)
      toast.info('Generation cancelled')
    } catch {
      toast.error('Failed to cancel')
    }
  }, [generationId])

  // Listen for WebSocket generation events
  useEffect(() => {
    if (!socket || !generationId) return

    const handleUpdate = (data: any) => {
      if (data.id !== generationId) return
      const steps = ['step_prepare', 'step_context', 'step_generate', 'step_save', 'step_done']
      const completedSteps = steps.filter(s => data[s] === 1).length
      setGenerationProgress({
        running: data.status === 'processing' || data.status === 'queued',
        status: data.status,
        step: completedSteps,
        total_steps: 5,
        error: data.error,
        type: data.type || generationType,
      })
    }

    const handleComplete = (data: any) => {
      if (data.id !== generationId) return
      unwatchGeneration(generationId)
      setGenerationProgress(null)
      setGenerationId(null)
      setGenerationType(null)
      // Store result for immediate display
      setGenerationResult(data)
      fetchResumes()
      toast.success('Generation complete!')
      // Clear result after 5 seconds
      setTimeout(() => setGenerationResult(null), 5000)
    }

    const handleError = (data: any) => {
      if (data.id !== generationId) return
      unwatchGeneration(generationId)
      setGenerationProgress(null)
      setGenerationId(null)
      setGenerationType(null)
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
  }, [socket, generationId, generationType, fetchResumes])

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    generationProgress, generationId, generationType, generationResult,
    fetchResumes, fetchLinkedin, generateResume, generateCover, cancelGeneration
  }
}
