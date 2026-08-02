'use client'

import dynamic from 'next/dynamic'

const CompaniesPage = dynamic(() => import('@/widgets/companies-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading companies...</div>,
  ssr: false,
})

export default function CompaniesRoute() {
  return <CompaniesPage />
}
