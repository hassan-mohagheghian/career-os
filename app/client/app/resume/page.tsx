'use client'

import dynamic from 'next/dynamic'

const ResumePage = dynamic(() => import('@/widgets/resume-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading resume...</div>,
  ssr: false,
})

export default function ResumeRoute() {
  return <ResumePage />
}
