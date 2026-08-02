'use client'

import dynamic from 'next/dynamic'

const SkillsPage = dynamic(() => import('@/widgets/skills-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading skills...</div>,
  ssr: false,
})

export default function SkillsRoute() {
  return <SkillsPage />
}
