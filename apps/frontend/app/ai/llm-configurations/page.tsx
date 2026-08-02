'use client'

import dynamic from 'next/dynamic'

const LlmConfigurationsTab = dynamic(
  () => import('@/features/ai/llm-configurations/LlmConfigurationsTab'),
  { ssr: false }
)

import MainLayout from '@/widgets/main-layout'

export default function LlmConfigurationsPage() {
  return (
    <MainLayout>
      <LlmConfigurationsTab />
    </MainLayout>
  )
}
