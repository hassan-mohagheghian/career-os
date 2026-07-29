'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'

const RulesTabContent = dynamic(
  () => import('@/features/rules/components/RulesTab').then(m => ({ default: m.default || m })),
  { ssr: false }
)

const API = '/api'

function RulesPageAdapter() {
  const [rules, setRules] = useState<any>(null)

  const fetchRules = useCallback(() => {
    fetch(`${API}/rules`)
      .then(r => r.json())
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
