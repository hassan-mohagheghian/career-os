import { Briefcase, Target, Rocket, House, FileText, Sun, Moon } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'

export default function Header({ jobAgg, jobsTotal, resumes, theme, onSwitchTab, onToggleTheme }) {
  return (
    <header className="h-12 border-b flex items-center px-4 gap-4 lg:gap-6 shrink-0 fixed top-0 left-0 lg:left-[170px] right-0 z-40 bg-card">
      <span className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent ml-10 lg:ml-0 whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity" onClick={() => onSwitchTab('jobs')}>Job Search</span>
      <div className="hidden sm:flex gap-3 text-[0.65rem] text-muted-foreground">
        <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" /><b className="text-foreground">{jobAgg.total || jobsTotal}</b> total</span>
        <span className="text-border">|</span>
        <span className="flex items-center gap-1"><Target className="w-3 h-3 text-green-500" /><b className="text-green-500">{jobAgg.high_match}</b> high match</span>
        <span className="text-border">|</span>
        <span className="flex items-center gap-1"><Rocket className="w-3 h-3 text-yellow-500" /><b className="text-yellow-500">{jobAgg.apply_now}</b> apply now</span>
        <span className="text-border">|</span>
        <span className="flex items-center gap-1"><House className="w-3 h-3 text-cyan-500" /><b className="text-cyan-500">{jobAgg.remote}</b> remote</span>
        <span className="text-border">|</span>
        <span className="flex items-center gap-1"><FileText className="w-3 h-3 text-primary" /><b className="text-primary">{resumes.filter(r => r.id?.startsWith('original')).length}</b> resume</span>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={onToggleTheme}>
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </div>
    </header>
  )
}
