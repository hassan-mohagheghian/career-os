'use client'

import { Briefcase, FileText, Sun, Moon, Buildings, Gear, List } from '@phosphor-icons/react'
import { usePathname, useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'

const GenerationHistoryDrawer = dynamic(() => import('@/shared/components/GenerationHistoryDrawer'), { ssr: false })

const FEATURES = [
  { id: 'jobs', icon: Briefcase, label: 'Jobs', color: 'text-blue-500' },
  { id: 'companies', icon: Buildings, label: 'Companies', color: 'text-emerald-500' },
  { id: 'skills', icon: List, label: 'Skills', color: 'text-amber-500' },
  { id: 'resume', icon: FileText, label: 'Resume', color: 'text-purple-500' },
  { id: 'rules', icon: Gear, label: 'Rules', color: 'text-cyan-500' },
]

export default function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const currentTab = pathname?.split('/')[1] || 'jobs'

  useEffect(() => setMounted(true), [])

  return (
    <>
      <header className="h-12 border-b flex items-center px-4 gap-3 lg:gap-5 shrink-0 fixed top-0 left-0 lg:left-[170px] right-0 z-40 bg-card">
        <span
          className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent ml-10 lg:ml-0 whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => router.push('/jobs')}
        >
          Job Search
        </span>

        <div className="hidden md:flex items-center gap-1">
          {FEATURES.map(f => {
            const Icon = f.icon
            const isActive = currentTab === f.id
            return (
              <button
                key={f.id}
                onClick={() => router.push(`/${f.id}`)}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all",
                  isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                <Icon className={cn("w-3.5 h-3.5", isActive ? "text-primary" : f.color)} />
                {f.label}
              </button>
            )
          })}
        </div>

        <div className="ml-auto flex items-center gap-1.5">
          {mounted && (
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
          )}
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setHistoryOpen(true)} title="Generation History">
            <List className="w-4 h-4" />
          </Button>
        </div>
      </header>

      <GenerationHistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} />
    </>
  )
}
