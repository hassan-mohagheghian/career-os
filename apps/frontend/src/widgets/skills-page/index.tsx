'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { setSearchParam, getSearchParam } from '@/shared/lib/url'

const SkillsTabContent = dynamic(
  () => import('@/features/skills/components/SkillsTab').then(m => ({ default: m.default || m })),
  { ssr: false }
)

function SkillsPageAdapter() {
  const [deepLinkSkill, setDeepLinkSkill] = useState<string | null>(null)

  useEffect(() => {
    const skill = getSearchParam('skill')
    if (skill) setDeepLinkSkill(skill)
  }, [])

  return (
    <SkillsTabContent
      deepLinkSkill={deepLinkSkill}
      onClearDeepLink={() => { setDeepLinkSkill(null); setSearchParam('skill', null) }}
      onSkillOpen={(name: string) => setSearchParam('skill', name)}
    />
  )
}

export default function SkillsPageWidget() {
  return (
    <MainLayout>
      <SkillsPageAdapter />
    </MainLayout>
  )
}
