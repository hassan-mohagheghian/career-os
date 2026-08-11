'use client'

import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'

const JobApplicationWorkspaceWidget = dynamic(
  () => import('@/widgets/job-application-workspace').then(m => m.default),
  {
    loading: () => (
      <div className="flex items-center justify-center h-64 text-muted-foreground">Loading application workspace...</div>
    ),
    ssr: false,
  }
)

export default function ApplicationRoute() {
  const params = useParams<{ job_id: string }>()
  const jobId = params?.job_id

  if (!jobId) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-red-500">Missing job id.</p>
      </div>
    )
  }

  return <JobApplicationWorkspaceWidget jobId={jobId} />
}
