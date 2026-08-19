'use client'

import dynamic from 'next/dynamic'

const PlaceholdersPage = dynamic(
  () => import('@/widgets/placeholders-page').then((m) => m.default || m),
  {
    loading: () => (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading placeholders...
      </div>
    ),
    ssr: false,
  }
)

export default function PlaceholdersRoute() {
  return <PlaceholdersPage />
}