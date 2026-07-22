import {
  TrendUp, Brain, BookOpen, ChartBar, ChartLineUp, Wrench, Stack,
  ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { TechCard, StackCard } from '@/components/TechCards'

export default function SkillsSection({ analysis, refreshing, onRefresh }) {
  const techStackData = analysis.techStack || []
  const techLearningData = analysis.techLearning || []
  const learningROI = analysis.learningROI || []
  const weaknesses = analysis.weaknesses || []

  const strongStack = techStackData.filter(t => t.mc === 'p1') || []
  const midStack = techStackData.filter(t => t.mc === 'p2') || []
  const weakStack = techStackData.filter(t => t.mc === 'p3' || t.mc === 'p4') || []
  const p1Tech = techLearningData.filter(t => t.pc === 'p1') || []
  const p2Tech = techLearningData.filter(t => t.pc === 'p2') || []
  const totalUsage = techStackData.reduce((sum, t) => sum + (t.level || 0), 0) || 0
  const avgLevel = techStackData.length ? (totalUsage / techStackData.length).toFixed(1) : 0

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Skill Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.skills} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.skills && "animate-spin")} /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-5 gap-3">
        {[
          { n: techStackData.length || 0, l: 'Total Skills', c: 'text-primary', icon: <Wrench className="w-5 h-5" /> },
          { n: strongStack.length, l: 'Strong Match', c: 'text-green-500', icon: <TrendUp className="w-5 h-5" /> },
          { n: midStack.length, l: 'Moderate', c: 'text-blue-500', icon: <Stack className="w-5 h-5" /> },
          { n: weakStack.length, l: 'Gaps', c: 'text-yellow-500', icon: <BookOpen className="w-5 h-5" /> },
          { n: `${avgLevel}/5`, l: 'Avg Level', c: 'text-purple-500', icon: <ChartBar className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className="text-lg mb-0.5">{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Wrench className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Current Tech Stack</h3>
              <Badge variant="secondary" className="text-[0.55rem]">{techStackData.length || 0} skills</Badge>
            </div>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
              {techStackData.map((t, i) => <StackCard key={i} tech={t} />)}
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Technologies to Master</h3>
              <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{techLearningData.length || 0} items</Badge>
            </div>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
              {techLearningData.map((t, i) => <TechCard key={i} tech={t} />)}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5 text-yellow-500" />
              <h3 className="font-extrabold text-sm">What to Learn</h3>
            </div>
            <div className="space-y-1.5">
              {p1Tech.map((t, i) => (
                <div key={`p1-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.reason}</span>
                  <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500 shrink-0">P1</Badge>
                </div>
              ))}
              {p2Tech.map((t, i) => (
                <div key={`p2-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.reason}</span>
                  <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-blue-500/15 text-blue-500 shrink-0">P2</Badge>
                </div>
              ))}
              {p1Tech.length === 0 && p2Tech.length === 0 && weaknesses.length === 0 && (
                <div className="text-xs text-muted-foreground">No major gaps</div>
              )}
            </div>
          </Card>

          {learningROI.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <ChartLineUp className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Learning ROI</h3>
              </div>
              <div className="space-y-1.5">
                {learningROI.slice(0, 5).map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold w-20 truncate">{item.skill}</span>
                    <div className="flex-1 h-[3px] rounded-full bg-muted">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${item.impactScore * 10}%` }} />
                    </div>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5 shrink-0", item.impactScore >= 7 ? "bg-green-500/15 text-green-500" : "bg-yellow-500/15 text-yellow-500")}>
                      {item.impactScore}/10
                    </Badge>
                    <span className="text-muted-foreground text-[0.55rem] shrink-0">{item.timeToLearn}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <ChartBar className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Level Distribution</h3>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Strong (5/5)', count: strongStack.length, color: 'bg-green-500' },
                { label: 'Good (4/5)', count: techStackData.filter(t => t.level === 4).length || 0, color: 'bg-blue-500' },
                { label: 'Moderate (3/5)', count: techStackData.filter(t => t.level === 3).length || 0, color: 'bg-yellow-500' },
                { label: 'Basic (2/5)', count: techStackData.filter(t => t.level === 2).length || 0, color: 'bg-orange-500' },
                { label: 'Beginner (1/5)', count: techStackData.filter(t => t.level === 1).length || 0, color: 'bg-red-500' },
              ].map((s, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-20 text-[0.6rem] text-muted-foreground">{s.label}</div>
                  <Progress value={techStackData.length ? (s.count / techStackData.length * 100) : 0} className="flex-1 h-2" />
                  <div className={cn("w-6 text-right text-[0.6rem] font-bold", s.color.replace('bg-', 'text-'))}>{s.count}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
