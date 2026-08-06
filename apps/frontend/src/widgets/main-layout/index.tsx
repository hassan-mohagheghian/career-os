'use client'

import { type ReactNode } from 'react'
import Header from '@/widgets/header'

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <div className="h-screen overflow-hidden bg-background text-foreground">
      <main className="flex flex-col overflow-hidden h-full">
        <Header />
        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
