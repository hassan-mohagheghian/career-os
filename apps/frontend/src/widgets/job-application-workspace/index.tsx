'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const ApplicationWorkspace = dynamic(
  () => import('@/features/job-application').then(m => ({ default: m.ApplicationWorkspace })),
  { ssr: false }
)

interface JobApplicationWorkspaceWidgetProps {
  jobId: string
}

export default function JobApplicationWorkspaceWidget({ jobId }: JobApplicationWorkspaceWidgetProps) {
  return (
    <MainLayout>
      <ApplicationWorkspace jobId={jobId} />
    </MainLayout>
  )
}
