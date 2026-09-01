'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { api } from '@/shared/api/http-client'

const RulesTabContent = dynamic(
  () => import('@/features/rules/components/RulesTab').then(m => ({ default: m.default || m })),
  { ssr: false }
)

function RulesPageAdapter() {
  const [rules, setRules] = useState<any>(null)

  const fetchRules = useCallback(() => {
    api.get('/rules')
      .then(setRules)
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchRules()
  }, [fetchRules])

  return <RulesTabContent rules={rules} onUpdate={fetchRules} />
}

export default function RulesPageWidget() {
  return (
    <MainLayout>
      <RulesPageAdapter />
    </MainLayout>
  )
}
