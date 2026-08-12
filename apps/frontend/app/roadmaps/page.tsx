'use client'

import dynamic from 'next/dynamic'

const MyRoadmapsPage = dynamic(() => import('@/widgets/my-roadmaps-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading roadmaps...</div>,
  ssr: false,
})

export default function RoadmapsRoute() {
  return <MyRoadmapsPage />
}