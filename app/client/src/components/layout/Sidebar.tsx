import { useState, type ReactNode } from 'react'
import { CaretRight, CaretDown } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

interface TabChild {
  id: string
  label: string
}

interface Tab {
  id: string
  section: string
  label?: string
  icon?: ReactNode
  badge?: number
  children?: TabChild[]
}

interface SidebarProps {
  sidebarOpen: boolean
  tabs: Tab[]
  tab: string
  onSwitchTab: (id: string, childId?: string) => void
  subTab?: string
  onSwitchSubTab?: (id: string) => void
  onClose: () => void
}

export default function Sidebar({ sidebarOpen, tabs, tab, onSwitchTab, subTab, onClose }: SidebarProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ 'career-intel': true })

  const toggleSection = (id: string) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <>
      {sidebarOpen && <div className="fixed inset-0 bg-black/40 z-[49] lg:hidden" onClick={onClose} />}
      <aside className={cn(
        "fixed lg:relative inset-y-0 left-0 z-[50] lg:z-auto border-r flex flex-col transition-all duration-200 bg-card",
        sidebarOpen ? "w-[170px]" : "w-0 overflow-hidden"
      )}>
        <div className="pt-12 lg:pt-0 flex-1 overflow-y-auto">
          {(['jobs', 'analysis', 'settings'] as const).map(section => (
            <div key={section}>
              <div className="px-3 py-2 text-xs uppercase tracking-wider text-muted-foreground">{section}</div>
              {tabs.filter(t => t.section === section).map(t => {
                const hasChildren = t.children && t.children.length > 0
                const isExpanded = expanded[t.id]
                const isActive = tab === t.id

                return (
                  <div key={t.id}>
                    <button
                      onClick={() => {
                        if (hasChildren) {
                          toggleSection(t.id)
                          onSwitchTab(t.id)
                        } else {
                          onSwitchTab(t.id)
                        }
                      }}
                      className={cn("flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition w-full text-left",
                        isActive ? "border-l-primary font-semibold text-primary" : "border-l-transparent text-muted-foreground"
                      )}
                    >
                      {t.icon && <span>{t.icon}</span>}
                      <span>{t.label}</span>
                      {t.badge && <Badge variant="default" className="ml-auto text-[0.55rem] h-5">{t.badge}</Badge>}
                      {hasChildren && (
                        <span className="ml-auto">
                          {isExpanded ? <CaretDown className="w-3 h-3" /> : <CaretRight className="w-3 h-3" />}
                        </span>
                      )}
                    </button>

                    {hasChildren && isExpanded && (
                      <div>
                        {t.children!.map(child => (
                          <button
                            key={child.id}
                            onClick={() => onSwitchTab(t.id, child.id)}
                            className={cn(
                              "flex items-center gap-2 pl-9 pr-3 py-1.5 text-xs border-l-3 transition w-full text-left",
                              subTab === child.id && tab === t.id
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
