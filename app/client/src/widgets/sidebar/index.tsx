'use client'

import { type ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Briefcase, Buildings, TreeStructure, FileText, Gear } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'

interface NavItem {
  id: string
  label: string
  icon: ReactNode
  badge?: number
}

const NAV_ITEMS: NavItem[] = [
  { id: 'jobs', label: 'Jobs', icon: <Briefcase className="w-4 h-4" /> },
  { id: 'companies', label: 'Companies', icon: <Buildings className="w-4 h-4" /> },
  { id: 'skills', label: 'Skills', icon: <TreeStructure className="w-4 h-4" /> },
  { id: 'resume', label: 'Resume', icon: <FileText className="w-4 h-4" /> },
  { id: 'rules', label: 'Rules', icon: <Gear className="w-4 h-4" /> },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
  jobsTotal?: number
}

export default function Sidebar({ open, onClose, jobsTotal }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const currentTab = pathname?.split('/')[1] || 'jobs'

  const handleNav = (id: string) => {
    router.push(`/${id}`)
    onClose()
  }

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/40 z-[49] lg:hidden" onClick={onClose} />}
      <aside className={cn(
        "fixed lg:relative inset-y-0 left-0 z-[50] lg:z-auto border-r flex flex-col transition-all duration-200 bg-card",
        open ? "w-[170px]" : "w-0 overflow-hidden"
      )}>
        <div className="pt-12 lg:pt-0 flex-1 overflow-y-auto">
          {(['jobs', 'settings'] as const).map(section => (
            <div key={section}>
              <div className="px-3 py-2 text-xs uppercase tracking-wider text-muted-foreground">{section}</div>
              {NAV_ITEMS.filter(t =>
                section === 'settings' ? ['resume', 'rules'].includes(t.id) : !['resume', 'rules'].includes(t.id)
              ).map(t => {
                const isActive = currentTab === t.id
                return (
                  <button
                    key={t.id}
                    onClick={() => handleNav(t.id)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition w-full text-left",
                      isActive ? "border-l-primary font-semibold text-primary" : "border-l-transparent text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <span>{t.icon}</span>
                    <span>{t.label}</span>
                    {t.id === 'jobs' && jobsTotal !== undefined && jobsTotal > 0 && (
                      <Badge variant="default" className="ml-auto text-2xs h-5">{jobsTotal}</Badge>
                    )}
                  </button>
                )
              })}
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}
