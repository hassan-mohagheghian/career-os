import { useState, useCallback } from 'react'
import { toast } from 'sonner'

const API = '/api'

export function useResume() {
  const [resumes, setResumes] = useState<any[]>([])
  const [linkedinProfiles, setLinkedinProfiles] = useState<any[]>([])
  const [generatingResume, setGeneratingResume] = useState(false)
  const [generatingCover, setGeneratingCover] = useState(false)

  const fetchResumes = useCallback(() => {
    return fetch(`${API}/resumes`).then(r => r.json()).then(setResumes)
  }, [])

  const fetchLinkedin = useCallback(() => {
    return fetch(`${API}/linkedin`).then(r => r.json()).then(setLinkedinProfiles)
  }, [])

  const generateResume = useCallback(async (num: number, setDrawer?: (fn: (prev: any) => any) => void) => {
    setGeneratingResume(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error || 'Failed'); return }
      setDrawer?.(prev => ({ ...prev, resume: { id: data.id, content: data.content, job_num: num } }))
      fetchResumes()
      toast.success('Resume generated!')
    } catch {
      toast.error('Generation failed')
    } finally {
      setGeneratingResume(false)
    }
  }, [fetchResumes])

  const generateCover = useCallback(async (num: number, setDrawer?: (fn: (prev: any) => any) => void) => {
    setGeneratingCover(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { toast.error(data.error || 'Failed'); return }
      setDrawer?.(prev => ({ ...prev, coverLetter: { id: data.id, content: data.content, job_num: num } }))
      fetchResumes()
      toast.success('Cover letter generated!')
    } catch {
      toast.error('Generation failed')
    } finally {
      setGeneratingCover(false)
    }
  }, [fetchResumes])

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    generatingResume, generatingCover,
    fetchResumes, fetchLinkedin, generateResume, generateCover
  }
}
