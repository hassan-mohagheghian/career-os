'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const ProfileImportContent = dynamic(
  () => import('@/features/candidate-v2/components/ProfileImportPage').then(m => ({ default: m.ProfileImportPage })),
  { ssr: false }
)

function CandidatePageAdapter() {
  return (
    <MainLayout>
      <ProfileImportContent />
    </MainLayout>
  )
}

const CandidatePageWidget = CandidatePageAdapter
export default CandidatePageWidget
