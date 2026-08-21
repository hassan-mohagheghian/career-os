'use client'

import dynamic from 'next/dynamic'

const CitiesPage = dynamic(() => import('@/widgets/cities-page').then(m => m.default || m), {
  loading: () => <div className="flex items-center justify-center h-64 text-muted-foreground">Loading cities...</div>,
  ssr: false,
})

export default function CitiesRoute() {
  return <CitiesPage />
}