'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const RoadmapDetailContent = dynamic(
  () => import('@/features/roadmaps/components/RoadmapDetailPage').then(m => ({ default: m.RoadmapDetailPage })),
  { ssr: false }
)

export default function RoadmapDetailPageWidget({ roadmapId }: { roadmapId: string }) {
  return (
    <MainLayout>
      <RoadmapDetailContent roadmapId={roadmapId} />
    </MainLayout>
  )
}