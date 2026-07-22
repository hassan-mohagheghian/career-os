import { Briefcase, Target, Rocket, House, FileText, Sun, Moon, Buildings, Brain, Gear } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const FEATURES = [
  { id: 'jobs', icon: Briefcase, label: 'Jobs', color: 'text-blue-500' },
  { id: 'companies', icon: Buildings, label: 'Companies', color: 'text-emerald-500' },
  { id: 'resume', icon: FileText, label: 'Resume', color: 'text-purple-500' },
  { id: 'intelligence', icon: Brain, label: 'Intelligence', color: 'text-amber-500' },
  { id: 'rules', icon: Gear, label: 'Rules', color: 'text-cyan-500' },
]

export default function Header({ jobAgg, jobsTotal, resumes, companies, theme, tab, onSwitchTab, onToggleTheme }) {
  const resumeCount = resumes?.filter(r => r.id?.startsWith('original')).length || 0
  const companyCount = companies?.length || 0

  return (
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
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[0.65rem] font-medium transition-all",
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

      {/* Stats */}
      <div className="hidden lg:flex items-center gap-3 ml-auto text-[0.65rem] text-muted-foreground">
        <StatBadge icon={Briefcase} value={jobAgg.total || jobsTotal} label="jobs" color="text-foreground" />
        <StatBadge icon={Target} value={jobAgg.high_match} label="match" color="text-green-500" />
        <StatBadge icon={Rocket} value={jobAgg.apply_now} label="apply" color="text-yellow-500" />
        <StatBadge icon={House} value={jobAgg.remote} label="remote" color="text-cyan-500" />
        <span className="text-border">|</span>
        <StatBadge icon={Buildings} value={companyCount} label="companies" color="text-emerald-500" />
        <StatBadge icon={FileText} value={resumeCount} label="resumes" color="text-purple-500" />
      </div>

      {/* Theme toggle */}
      <div className="ml-auto lg:ml-0 flex items-center">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={onToggleTheme}>
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </div>
    </header>
  )
}

function StatBadge({ icon: Icon, value, label, color }) {
  return (
    <span className="flex items-center gap-1">
      <Icon className={cn("w-3 h-3", color)} />
      <b className={color}>{value || 0}</b>
      <span className="opacity-70">{label}</span>
    </span>
  )
}
