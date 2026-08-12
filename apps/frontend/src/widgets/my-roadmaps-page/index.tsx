'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const MyRoadmapsContent = dynamic(
  () => import('@/features/roadmaps/components/MyRoadmapsPage').then(m => ({ default: m.MyRoadmapsPage })),
  { ssr: false }
)

export default function MyRoadmapsPageWidget() {
  return (
    <MainLayout>
      <MyRoadmapsContent />
    </MainLayout>
  )
}