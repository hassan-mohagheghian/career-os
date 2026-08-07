'use client'

import dynamic from 'next/dynamic'

const CandidatePage = dynamic(() => import('@/widgets/candidate-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading candidate profile...</div>,
  ssr: false,
})

export default function CandidateRoute() {
  return <CandidatePage />
}
