'use client'

import dynamic from 'next/dynamic'

const JobsPage = dynamic(() => import('@/widgets/jobs-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading jobs...</div>,
  ssr: false,
})

export default function JobsRoute() {
  return <JobsPage />
}
