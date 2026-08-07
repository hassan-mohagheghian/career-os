'use client'

import { type ReactNode } from 'react'
import Sidebar from '@/widgets/sidebar'

export default function MainLayout({ children }: { children: ReactNode }) {
  return <Sidebar>{children}</Sidebar>
}
