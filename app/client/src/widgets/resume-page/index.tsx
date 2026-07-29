'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useEffect, useState } from 'react'

const ResumeTabContent = dynamic(
  () => import('@/features/resume/components/ResumeTab').then(m => ({ default: m.default || m })),
  { ssr: false }
)

const API = '/api'

function ResumePageAdapter() {
  const [resumes, setResumes] = useState<any[]>([])
  const [linkedinProfiles, setLinkedinProfiles] = useState<any[]>([])

  const fetchResumes = () => {
    fetch(`${API}/resumes`).then(r => r.json()).then(setResumes).catch(() => {})
  }

  const fetchLinkedin = () => {
    fetch(`${API}/linkedin`).then(r => r.json()).then(setLinkedinProfiles).catch(() => {})
  }

  useEffect(() => {
    fetchResumes()
    fetchLinkedin()
  }, [])

  return (
    <ResumeTabContent
      resumes={resumes}
      linkedinProfiles={linkedinProfiles}
      onRefreshResumes={fetchResumes}
      onRefreshLinkedin={fetchLinkedin}
    />
  )
}

export default function ResumePageWidget() {
  return (
    <MainLayout>
      <ResumePageAdapter />
    </MainLayout>
  )
}
