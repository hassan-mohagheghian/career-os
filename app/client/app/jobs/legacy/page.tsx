'use client'
import dynamic from 'next/dynamic'
import { LegacyBanner } from '@/widgets/jobs-page-legacy-banner'

const JobsPage = dynamic(() => import('@/widgets/jobs-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading jobs...</div>,
  ssr: false,
})

export default function JobsLegacyRoute() {
  return (
    <>
      <LegacyBanner />
      <JobsPage />
    </>
  )
}
