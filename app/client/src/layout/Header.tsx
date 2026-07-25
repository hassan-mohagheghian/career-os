import { Briefcase, FileText, Sun, Moon, Buildings, Gear, Lightbulb, List } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import { useState } from 'react'
import GenerationHistoryDrawer from '@/shared/components/GenerationHistoryDrawer'

const FEATURES = [
  { id: 'jobs', icon: Briefcase, label: 'Jobs', color: 'text-blue-500' },
  { id: 'companies', icon: Buildings, label: 'Companies', color: 'text-emerald-500' },
  { id: 'resume', icon: FileText, label: 'Resume', color: 'text-purple-500' },
  { id: 'insights', icon: Lightbulb, label: 'Insights', color: 'text-amber-500' },
  { id: 'rules', icon: Gear, label: 'Rules', color: 'text-cyan-500' },
]

interface HeaderProps {
  theme: string
  tab: string
  onSwitchTab: (id: string) => void
  onToggleTheme: () => void
}

export default function Header({ theme, tab, onSwitchTab, onToggleTheme }: HeaderProps) {
  const [historyOpen, setHistoryOpen] = useState(false)

  return (
    <>
      <header className="h-12 border-b flex items-center px-4 gap-3 lg:gap-5 shrink-0 fixed top-0 left-0 lg:left-[170px] right-0 z-40 bg-card">
        {/* Brand */}
        <span className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent ml-10 lg:ml-0 whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity" onClick={() => onSwitchTab('jobs')}>
          Job Search
        </span>

        {/* Feature tabs */}
        <div className="hidden md:flex items-center gap-1">
          {FEATURES.map(f => {
            const Icon = f.icon
            const isActive = tab === f.id
            return (
              <button
                key={f.id}
                onClick={() => onSwitchTab(f.id)}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                <Icon className={cn("w-3.5 h-3.5", isActive ? "text-primary" : f.color)} />
                {f.label}
              </button>
            )
          })}
        </div>

        {/* Theme + History toggle — always right-aligned */}
        <div className="ml-auto flex items-center gap-1.5">
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={onToggleTheme}>
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setHistoryOpen(true)} title="Generation History">
            <List className="w-4 h-4" />
          </Button>
        </div>
      </header>

      <GenerationHistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} />
    </>
  )
}
