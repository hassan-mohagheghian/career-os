'use client'

import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'

const RoadmapDetailPage = dynamic(
  () => import('@/widgets/roadmap-detail-page').then((m) => m.default),
  {
    loading: () => (
      <div className="flex items-center justify-center h-64 text-muted-foreground">Loading roadmap...</div>
    ),
    ssr: false,
  }
)

export default function RoadmapDetailRoute() {
  const params = useParams<{ roadmap_id: string }>()
  const roadmapId = params?.roadmap_id

  if (!roadmapId) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-red-500">Missing roadmap id.</p>
      </div>
    )
  }

  return <RoadmapDetailPage roadmapId={roadmapId} />
}