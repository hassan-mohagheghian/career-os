import {
  Briefcase, ChartBar, Target, Rocket, House, IdentificationCard,
  MapPin, Wrench, Lightbulb, ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function MarketSection({ analysis, jobs, jobsTotal, refreshing, onRefresh, onOpenDrawer }) {
  const market = analysis.market || {}
  const jobsByCity = market.jobsByCity || []
  const techDemand = market.techDemand || []
  const visaDist = market.visaDistribution || []
  const scoreDist = market.scoreDistribution || []
  const insights = market.insights || []

  const highMatch = jobs.filter(j => j.match === 'High').length
  const applyNow = jobs.filter(j => ['A', 'A+', 'A++'].includes(j.score)).length
  const remoteJobs = jobs.filter(j => j.work_type === 'Remote').length
  const visaReady = jobs.filter(j => j.visa === 'BEST' || j.visa === 'Strong').length

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Market Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.market} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.market && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { n: jobsTotal || jobs.length, l: 'Total Jobs', c: 'text-primary', icon: <Briefcase className="w-5 h-5" /> },
          { n: highMatch, l: 'High Match', c: 'text-green-500', icon: <Target className="w-5 h-5" /> },
          { n: applyNow, l: 'Apply Now', c: 'text-yellow-500', icon: <Rocket className="w-5 h-5" /> },
          { n: remoteJobs, l: 'Remote', c: 'text-cyan-500', icon: <House className="w-5 h-5" /> },
          { n: visaReady, l: 'Visa Ready', c: 'text-purple-500', icon: <IdentificationCard className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Jobs by City */}
          {jobsByCity.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Jobs by City</h3>
              </div>
              <div className="space-y-2">
                {jobsByCity.map((city, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="w-20 text-[0.65rem] text-muted-foreground truncate">{city.name}</div>
                    <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                      <div className="h-full bg-primary/60 rounded flex items-center px-2" style={{ width: `${Math.max(city.percentage || (city.count / (jobsTotal || jobs.length) * 100), 5)}%` }}>
                        <span className="text-[0.55rem] font-bold text-white">{city.count}</span>
                      </div>
                    </div>
                    <div className="w-10 text-right text-[0.6rem] font-bold text-primary">{Math.round(city.percentage || (city.count / (jobsTotal || jobs.length) * 100))}%</div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Tech Demand */}
          {techDemand.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Wrench className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Technology Demand</h3>
              </div>
              <div className="space-y-2">
                {techDemand.slice(0, 10).map((tech, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="w-24 text-[0.65rem] text-muted-foreground truncate">{tech.name}</div>
                    <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                      <div className="h-full bg-green-500/60 rounded flex items-center px-2" style={{ width: `${Math.max(tech.percentage || (tech.count / (jobsTotal || jobs.length) * 100), 5)}%` }}>
                        <span className="text-[0.55rem] font-bold text-white">{tech.count}</span>
                      </div>
                    </div>
                    <div className="w-10 text-right text-[0.6rem] font-bold text-green-500">{Math.round(tech.percentage || (tech.count / (jobsTotal || jobs.length) * 100))}%</div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Score Distribution */}
          {scoreDist.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <ChartBar className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Score Distribution</h3>
                {market.avgOverallScore && <Badge variant="secondary" className="text-[0.5rem]">Avg: {Math.round(market.avgOverallScore)}</Badge>}
              </div>
              <div className="flex items-end gap-3 h-32">
                {scoreDist.map((s, i) => {
                  const maxCount = Math.max(...scoreDist.map(x => x.count))
                  const height = maxCount > 0 ? (s.count / maxCount * 100) : 0
                  const colors = { 'A++': 'bg-emerald-500', 'A+': 'bg-green-500', 'A': 'bg-blue-500', 'B': 'bg-yellow-500', 'C': 'bg-orange-500', 'D': 'bg-red-500' }
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div className="text-[0.55rem] font-bold">{s.count}</div>
                      <div className={cn("w-full rounded-t", colors[s.grade] || 'bg-gray-500')} style={{ height: `${height}%` }} />
                      <div className="text-[0.55rem] font-bold">{s.grade}</div>
                    </div>
                  )
                })}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Visa Distribution */}
          {visaDist.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <IdentificationCard className="w-5 h-5 text-purple-500" />
                <h3 className="font-extrabold text-sm">Visa Distribution</h3>
              </div>
              <div className="space-y-2">
                {visaDist.map((v, i) => {
                  const colors = { 'BEST': 'bg-green-500', 'Strong': 'bg-green-400', 'Good': 'bg-yellow-500', 'Moderate': 'bg-orange-500', 'Uncertain': 'bg-gray-500' }
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-16 text-[0.6rem] text-muted-foreground">{v.visa}</div>
                      <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
                        <div className={cn("h-full rounded", colors[v.visa] || 'bg-gray-500')} style={{ width: `${v.percentage || (v.count / (jobsTotal || jobs.length) * 100)}%` }} />
                      </div>
                      <div className="w-10 text-right text-[0.6rem] font-bold">{v.count}</div>
                    </div>
                  )
                })}
              </div>
            </Card>
          )}

          {/* AI Insights */}
          {insights.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                <h3 className="font-extrabold text-sm">Market Insights</h3>
              </div>
              <div className="space-y-3">
                {insights.map((insight, i) => (
                  <div key={i} className="p-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 space-y-1">
                    <div className="text-[0.6rem] font-bold text-yellow-500">Observation</div>
                    <div className="text-[0.6rem] text-muted-foreground">{insight.observation}</div>
                    {insight.evidence && <div className="text-[0.55rem] text-muted-foreground/70"><strong>Evidence:</strong> {insight.evidence}</div>}
                    {insight.action && <div className="text-[0.55rem] text-primary"><strong>Action:</strong> {insight.action}</div>}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
