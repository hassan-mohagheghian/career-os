'use client'

import { type ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Briefcase, Buildings, TreeStructure, FileText, Gear, Brain } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'

interface NavChild {
  id: string
  label: string
}

interface NavItem {
  id: string
  label: string
  icon: ReactNode
  section: 'jobs' | 'settings'
  badge?: number
  children?: NavChild[]
}

const NAV_ITEMS: NavItem[] = [
  { id: 'jobs', label: 'Jobs', icon: <Briefcase className="w-4 h-4" />, section: 'jobs' },
  { id: 'companies', label: 'Companies', icon: <Buildings className="w-4 h-4" />, section: 'jobs' },
  { id: 'skills', label: 'Skills', icon: <TreeStructure className="w-4 h-4" />, section: 'jobs' },
  { id: 'resume', label: 'Resume', icon: <FileText className="w-4 h-4" />, section: 'settings' },
  {
    id: 'ai',
    label: 'AI',
    icon: <Brain className="w-4 h-4" />,
    section: 'settings',
    children: [{ id: 'llm-configurations', label: 'LLM Configurations' }],
  },
  { id: 'rules', label: 'Rules', icon: <Gear className="w-4 h-4" />, section: 'settings' },
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
  const currentSubTab = pathname?.split('/')[2] || null

  const handleNav = (id: string, childId?: string) => {
    const path = childId ? `/${id}/${childId}` : `/${id}`
    router.push(path)
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
              {NAV_ITEMS.filter(t => t.section === section).map(t => {
                const hasChildren = t.children && t.children.length > 0
                const isActive = currentTab === t.id

                return (
                  <div key={t.id}>
                    <button
                      onClick={() => handleNav(t.id)}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition w-full text-left",
                        isActive ? "border-l-primary font-semibold text-primary" : "border-l-transparent text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <span>{t.icon}</span>
                      <span>{t.label}</span>
                      {t.badge !== undefined && t.badge > 0 && (
                        <Badge variant="default" className="ml-auto text-2xs h-5">{t.badge}</Badge>
                      )}
                    </button>

                    {hasChildren && (
                      <div>
                        {t.children!.map(child => (
                          <button
                            key={child.id}
                            onClick={() => handleNav(t.id, child.id)}
                            className={cn(
                              "flex items-center gap-2 pl-9 pr-3 py-1.5 text-xs border-l-3 transition w-full text-left",
                              currentSubTab === child.id && isActive
                                ? "border-l-primary font-semibold text-primary"
                                : "border-l-transparent text-muted-foreground hover:text-foreground"
                            )}
                          >
                            {child.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}
