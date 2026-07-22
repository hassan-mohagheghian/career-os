import { useState, useCallback } from 'react'

const API = '/api'

export function useResume(showToast) {
  const [resumes, setResumes] = useState([])
  const [linkedinProfiles, setLinkedinProfiles] = useState([])
  const [generatingResume, setGeneratingResume] = useState(false)
  const [generatingCover, setGeneratingCover] = useState(false)

  const fetchResumes = useCallback(() => {
    return fetch(`${API}/resumes`).then(r => r.json()).then(setResumes)
  }, [])

  const fetchLinkedin = useCallback(() => {
    return fetch(`${API}/linkedin`).then(r => r.json()).then(setLinkedinProfiles)
  }, [])

  const generateResume = useCallback(async (num, setDrawer) => {
    setGeneratingResume(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { showToast?.(data.error || 'Failed'); return }
      setDrawer?.(prev => ({ ...prev, resume: { id: data.id, content: data.content, job_num: num } }))
      fetchResumes()
      showToast?.('Resume generated!')
    } catch (e) {
      showToast?.('Generation failed')
    } finally {
      setGeneratingResume(false)
    }
  }, [fetchResumes, showToast])

  const generateCover = useCallback(async (num, setDrawer) => {
    setGeneratingCover(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { showToast?.(data.error || 'Failed'); return }
      setDrawer?.(prev => ({ ...prev, coverLetter: { id: data.id, content: data.content, job_num: num } }))
      fetchResumes()
      showToast?.('Cover letter generated!')
    } catch (e) {
      showToast?.('Generation failed')
    } finally {
      setGeneratingCover(false)
    }
  }, [fetchResumes, showToast])

  return {
    resumes, setResumes, linkedinProfiles, setLinkedinProfiles,
    generatingResume, generatingCover,
    fetchResumes, fetchLinkedin, generateResume, generateCover
  }
}
