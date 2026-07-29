'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const SkillsTabContent = dynamic(
  () => import('@/features/skills/components/SkillsTab').then(m => ({ default: m.default || m })),
  { ssr: false }
)

function SkillsPageAdapter() {
  return <SkillsTabContent deepLinkSkill={null} onClearDeepLink={() => {}} />
}

export default function SkillsPageWidget() {
  return (
    <MainLayout>
      <SkillsPageAdapter />
    </MainLayout>
  )
}
