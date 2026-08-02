'use client'

import dynamic from 'next/dynamic'

const RulesPage = dynamic(() => import('@/widgets/rules-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading rules...</div>,
  ssr: false,
})

export default function RulesRoute() {
  return <RulesPage />
}
