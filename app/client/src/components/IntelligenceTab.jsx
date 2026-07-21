import { useState } from 'react'
import {
  Briefcase, ChartBar, Target, Brain, Rocket, House, TrendUp,
  BookOpen, ChartLineUp, Wrench, Clipboard, Lightning, Globe, Link,
  Users, IdentificationCard, FileText, ArrowsClockwise, CheckCircle,
  MagnifyingGlass, Lightbulb, Stack, Buildings, MapPin
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { CompactJobCard } from '@/components/ProcessedCards'
import { TechCard, StackCard } from '@/components/TechCards'

export default function IntelligenceTab({ analysis, jobs, resumes, linkedinProfiles, cities, rules, intelligenceSubTab, refreshing, onSetIntelligenceSubTab, onRefreshAll, onRefreshMarket, onRefreshOpportunity, onRefreshStrategy, onRefreshNetworking, onRefreshSkills, onOpenDrawer }) {
  const analysisData = analysis?.analysis || {}
  const hasAnalysis = !!analysis?.analysis

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-extrabold">Career Intelligence</h2>
          <Tabs value={intelligenceSubTab} onValueChange={onSetIntelligenceSubTab}>
            <TabsList className="bg-muted">
              <TabsTrigger value="market"><ChartBar className="w-4 h-4 mr-1.5" />Market</TabsTrigger>
              <TabsTrigger value="opportunity"><Target className="w-4 h-4 mr-1.5" />Opportunity</TabsTrigger>
              <TabsTrigger value="strategy"><Rocket className="w-4 h-4 mr-1.5" />Strategy</TabsTrigger>
              <TabsTrigger value="skills"><Brain className="w-4 h-4 mr-1.5" />Skills</TabsTrigger>
              <TabsTrigger value="company"><Buildings className="w-4 h-4 mr-1.5" />Company</TabsTrigger>
              <TabsTrigger value="networking"><Users className="w-4 h-4 mr-1.5" />Networking</TabsTrigger>
            </TabsList>
          </Tabs>
          <p className="text-xs text-muted-foreground">
            {analysis?.created_at && <span>Last updated: {new Date(analysis.created_at).toLocaleString()}</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={onRefreshAll} disabled={refreshing.analysis} variant={refreshing.analysis ? "secondary" : "outline"} size="sm" className="gap-1.5">
            <ArrowsClockwise className={cn("w-3.5 h-3.5", refreshing.analysis && "animate-spin")} />
            {refreshing.analysis ? 'Updating...' : 'Refresh All'}
          </Button>
        </div>
      </div>

      {!hasAnalysis && !refreshing.analysis && (
        <Card className="p-8 text-center border-dashed">
          <Brain className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-sm font-semibold mb-1">No intelligence data yet</p>
          <p className="text-xs text-muted-foreground mb-4">Click "Refresh All" to generate insights from your {jobs.length} processed jobs.</p>
          <Button onClick={onRefreshAll} size="sm" className="gap-1.5">
            <ArrowsClockwise className="w-3.5 h-3.5" /> Generate Intelligence
          </Button>
        </Card>
      )}

      {intelligenceSubTab === 'market' && (
        <MarketSection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshMarket} onOpenDrawer={onOpenDrawer} />
      )}

      {intelligenceSubTab === 'opportunity' && (
        <OpportunitySection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshOpportunity} onOpenDrawer={onOpenDrawer} />
      )}

      {intelligenceSubTab === 'strategy' && (
        <StrategySection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshStrategy} />
      )}

      {intelligenceSubTab === 'skills' && (
        <SkillsSection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshSkills} />
      )}

      {intelligenceSubTab === 'company' && (
        <CompanySection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshAll} onOpenDrawer={onOpenDrawer} />
      )}

      {intelligenceSubTab === 'networking' && (
        <NetworkingSection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshNetworking} />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// MARKET INTELLIGENCE
// ═══════════════════════════════════════════════════════════════

function MarketSection({ analysis, jobs, refreshing, onRefresh, onOpenDrawer }) {
  const market = analysis.market || {}
  const jobsByCity = market.jobsByCity || []
  const techDemand = market.techDemand || []
  const visaDist = market.visaDistribution || []
  const scoreDist = market.scoreDistribution || []
  const insights = market.insights || []
  const overview = analysis.overview || {}

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
          { n: jobs.length, l: 'Total Jobs', c: 'text-primary', icon: <Briefcase className="w-5 h-5" /> },
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
                      <div className="h-full bg-primary/60 rounded flex items-center px-2" style={{ width: `${Math.max(city.percentage || (city.count / jobs.length * 100), 5)}%` }}>
                        <span className="text-[0.55rem] font-bold text-white">{city.count}</span>
                      </div>
                    </div>
                    <div className="w-10 text-right text-[0.6rem] font-bold text-primary">{Math.round(city.percentage || (city.count / jobs.length * 100))}%</div>
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
                      <div className="h-full bg-green-500/60 rounded flex items-center px-2" style={{ width: `${Math.max(tech.percentage || (tech.count / jobs.length * 100), 5)}%` }}>
                        <span className="text-[0.55rem] font-bold text-white">{tech.count}</span>
                      </div>
                    </div>
                    <div className="w-10 text-right text-[0.6rem] font-bold text-green-500">{Math.round(tech.percentage || (tech.count / jobs.length * 100))}%</div>
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
                        <div className={cn("h-full rounded", colors[v.visa] || 'bg-gray-500')} style={{ width: `${v.percentage || (v.count / jobs.length * 100)}%` }} />
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

// ═══════════════════════════════════════════════════════════════
// OPPORTUNITY RADAR
// ═══════════════════════════════════════════════════════════════

function OpportunitySection({ analysis, jobs, refreshing, onRefresh, onOpenDrawer }) {
  const opportunity = analysis.opportunity || {}
  const matrix = opportunity.matrix || {}
  const topOpps = opportunity.topOpportunities || []
  const insights = opportunity.insights || []

  const quadrants = [
    { key: 'highFitHighSuccess', label: 'Apply Now', color: 'bg-green-500', textColor: 'text-green-500', borderColor: 'border-green-500/30', icon: <Rocket className="w-4 h-4" /> },
    { key: 'highFitMediumSuccess', label: 'Customize', color: 'bg-blue-500', textColor: 'text-blue-500', borderColor: 'border-blue-500/30', icon: <Target className="w-4 h-4" /> },
    { key: 'mediumFitHighSuccess', label: 'Consider', color: 'bg-yellow-500', textColor: 'text-yellow-500', borderColor: 'border-yellow-500/30', icon: <Lightbulb className="w-4 h-4" /> },
    { key: 'lowFit', label: 'Skip', color: 'bg-gray-500', textColor: 'text-gray-500', borderColor: 'border-gray-500/30', icon: <Lightning className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Opportunity Radar</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.opportunity} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.opportunity && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Opportunity Matrix */}
      <div className="grid grid-cols-2 gap-3">
        {quadrants.map((q) => {
          const data = matrix[q.key] || { count: 0, jobs: [] }
          return (
            <Card key={q.key} className={cn("p-4 border", q.borderColor)}>
              <div className="flex items-center gap-2 mb-2">
                <div className={q.textColor}>{q.icon}</div>
                <h4 className="font-bold text-sm">{q.label}</h4>
                <Badge variant="secondary" className={cn("text-[0.5rem]", q.textColor)}>{data.count} jobs</Badge>
              </div>
              {data.jobs && data.jobs.length > 0 ? (
                <div className="space-y-1.5">
                  {data.jobs.slice(0, 4).map((job, i) => (
                    <div key={i} className="flex items-center justify-between text-[0.6rem] p-1.5 rounded hover:bg-muted transition">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-semibold truncate">{job.company}</span>
                        <span className="text-muted-foreground truncate">{job.role}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">F:{job.fitScore}</Badge>
                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">S:{job.successScore}</Badge>
                      </div>
                    </div>
                  ))}
                  {data.jobs.length > 4 && <div className="text-[0.5rem] text-muted-foreground">+{data.jobs.length - 4} more</div>}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">No jobs in this category</div>
              )}
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Top Opportunities Table */}
          {topOpps.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-green-500" />
                <h3 className="font-extrabold text-sm">Top Opportunities</h3>
                <Badge variant="secondary" className="text-[0.5rem]">{topOpps.length} ranked</Badge>
              </div>
              <div className="space-y-1.5">
                {topOpps.map((opp, i) => (
                  <div key={i} className="flex items-center gap-3 text-[0.6rem] p-2 rounded hover:bg-muted transition border-l-2 border-primary">
                    <div className="w-6 text-center font-bold text-primary">#{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold">{opp.company}</div>
                      <div className="text-muted-foreground truncate">{opp.role} · {opp.location}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500">F:{opp.fitScore}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-blue-500/15 text-blue-500">S:{opp.successScore}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-purple-500/15 text-purple-500">O:{opp.overallScore}</Badge>
                    </div>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5 shrink-0",
                      opp.action === 'Apply Now' ? "bg-green-500/15 text-green-500" :
                      opp.action === 'Customize' ? "bg-blue-500/15 text-blue-500" :
                      opp.action === 'Consider' ? "bg-yellow-500/15 text-yellow-500" :
                      "bg-gray-500/15 text-gray-500"
                    )}>{opp.action}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Insights */}
          {insights.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                <h3 className="font-extrabold text-sm">Opportunity Insights</h3>
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

// ═══════════════════════════════════════════════════════════════
// APPLICATION STRATEGY
// ═══════════════════════════════════════════════════════════════

function StrategySection({ analysis, refreshing, onRefresh }) {
  const strategy = analysis.strategy || []
  const strengths = analysis.strengths || []
  const improvements = analysis.improvements || []
  const applyUrgency = analysis.apply_urgency || []
  const goals = analysis.goals || []
  const searchSummary = analysis.searchSummary || {}

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Application Strategy</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.strategy} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.strategy && "animate-spin")} /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clipboard className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Action Items</h3>
            </div>
            <div className="space-y-2">
              {strategy.map((g, i) => (
                <div key={`s-${i}`} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-muted border-l-2 border-primary">
                  <span className="shrink-0 text-primary text-lg">{g.icon}</span>
                  <div>
                    <div className="font-bold text-xs">{g.title}</div>
                    <div className="text-[0.6rem] text-muted-foreground">{g.description}</div>
                  </div>
                </div>
              ))}
              {improvements.map((item, i) => (
                <div key={`i-${i}`} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-muted border-l-2 border-orange-500">
                  <Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5 text-orange-500" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs">{item.area}</span>
                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5", item.priority === 'high' ? "bg-red-500/15 text-red-500" : item.priority === 'medium' ? "bg-yellow-500/15 text-yellow-500" : "bg-blue-500/15 text-blue-500")}>
                        {item.priority}
                      </Badge>
                    </div>
                    <div className="text-[0.6rem] text-muted-foreground">{item.action}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {applyUrgency.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightning className="w-5 h-5 text-yellow-500" />
                <h3 className="font-extrabold text-sm">Urgent Applications</h3>
              </div>
              <div className="space-y-1.5">
                {applyUrgency.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{item.company}</span>
                    <span className="text-muted-foreground">- {item.reason}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {goals.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-cyan-500" />
                <h3 className="font-extrabold text-sm">Goals & Best Practices</h3>
              </div>
              <div className="space-y-2">
                {goals.map((g, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                    <Target className="w-3.5 h-3.5 shrink-0 mt-0.5 text-cyan-500" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-bold text-xs text-cyan-500">{g.title}</span>
                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">{g.timeline}</Badge>
                      </div>
                      <div className="text-[0.6rem] text-muted-foreground">{g.bestPractice}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendUp className="w-5 h-5 text-green-500" />
              <h3 className="font-extrabold text-sm">Your Strengths</h3>
            </div>
            {strengths.length > 0 ? (
              <div className="space-y-1.5">
                {strengths.map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    <span className="font-semibold">{t.name}</span>
                    <span className="text-muted-foreground">- {t.detail}</span>
                  </div>
                ))}
              </div>
            ) : <div className="text-xs text-muted-foreground">No strong matches yet</div>}
          </Card>

          {searchSummary.totalSearched > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <MagnifyingGlass className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Search Summary</h3>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Jobs Analyzed</span>
                  <span className="font-bold">{searchSummary.totalSearched}</span>
                </div>
                {searchSummary.topCompanies?.length > 0 && (
                  <div className="mt-1.5">
                    <div className="text-[0.6rem] text-muted-foreground mb-1">Top Companies</div>
                    <div className="flex flex-wrap gap-1">
                      {searchSummary.topCompanies.slice(0, 5).map((c, i) => (
                        <Badge key={i} variant="secondary" className="text-[0.5rem]">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {searchSummary.pattern && (
                  <div className="mt-2 p-2 rounded bg-muted text-[0.6rem] text-muted-foreground">
                    {searchSummary.pattern}
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// SKILL INTELLIGENCE
// ═══════════════════════════════════════════════════════════════

function SkillsSection({ analysis, refreshing, onRefresh }) {
  const techStackData = analysis.techStack || []
  const techLearningData = analysis.techLearning || []
  const skillJobFit = analysis.skillJobFit || []
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
              <Gear className="w-5 h-5 text-primary" />
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

// ═══════════════════════════════════════════════════════════════
// COMPANY INTELLIGENCE
// ═══════════════════════════════════════════════════════════════

function CompanySection({ analysis, jobs, refreshing, onRefresh, onOpenDrawer }) {
  const visaCompanies = analysis.visa_companies || []
  const cities = analysis.cities || []

  // Build company rankings from jobs
  const companyMap = {}
  jobs.forEach(j => {
    if (!companyMap[j.company]) {
      companyMap[j.company] = { company: j.company, jobs: [], totalFit: 0, totalSuccess: 0, totalOverall: 0, visa: j.visa, location: j.location }
    }
    companyMap[j.company].jobs.push(j)
    companyMap[j.company].totalFit += (j.fit_score || 0)
    companyMap[j.company].totalSuccess += (j.success_score || 0)
    companyMap[j.company].totalOverall += (j.overall_score || 0)
  })

  const companyRankings = Object.values(companyMap)
    .map(c => ({
      ...c,
      avgFit: c.jobs.length ? Math.round(c.totalFit / c.jobs.length) : 0,
      avgSuccess: c.jobs.length ? Math.round(c.totalSuccess / c.jobs.length) : 0,
      avgOverall: c.jobs.length ? Math.round(c.totalOverall / c.jobs.length) : 0,
      matchCount: c.jobs.filter(j => j.match === 'High').length,
    }))
    .sort((a, b) => b.avgOverall - a.avgOverall)
    .slice(0, 15)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Company Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Company Rankings */}
          {companyRankings.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Buildings className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Company Rankings</h3>
                <Badge variant="secondary" className="text-[0.5rem]">{companyRankings.length} companies</Badge>
              </div>
              <div className="space-y-1.5">
                {companyRankings.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 text-[0.6rem] p-2 rounded hover:bg-muted transition">
                    <div className="w-6 text-center font-bold text-primary">#{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold">{c.company}</div>
                      <div className="text-muted-foreground">{c.jobs.length} roles · {c.location}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5">F:{c.avgFit}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5">S:{c.avgSuccess}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-purple-500/15 text-purple-500">O:{c.avgOverall}</Badge>
                    </div>
                    {c.matchCount > 0 && <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500">{c.matchCount} high</Badge>}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Visa Companies */}
          {visaCompanies.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <IdentificationCard className="w-5 h-5 text-purple-500" />
                <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
              </div>
              <div className="space-y-1.5">
                {visaCompanies.slice(0, 8).map((j, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{j.company}</span>
                    <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{j.visa}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Cities */}
          {cities.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Top Cities</h3>
              </div>
              <div className="space-y-1.5">
                {cities.slice(0, 6).map((c, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{c.name}</span>
                    <span className="text-muted-foreground">{c.jobs} jobs ({c.percentage}%)</span>
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

// ═══════════════════════════════════════════════════════════════
// NETWORKING INTELLIGENCE
// ═══════════════════════════════════════════════════════════════

function NetworkingSection({ analysis, refreshing, onRefresh }) {
  const networking = analysis.networking || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Networking Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.networking} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.networking && "animate-spin")} /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Networking Targets</h3>
            </div>
            <p className="text-[0.6rem] text-muted-foreground mb-3">Top companies to connect with on LinkedIn.</p>
            <div className="space-y-3">
              {networking.map((item, i) => (
                <div key={i} className="rounded-lg border p-3 space-y-2.5 hover:shadow transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm">{item.company}</span>
                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                        item.score === 'A++' || item.score === 'A+' ? "bg-green-500/15 text-green-500" :
                        item.score === 'A' ? "bg-blue-500/15 text-blue-500" :
                        "bg-yellow-500/15 text-yellow-500"
                      )}>{item.score}</Badge>
                    </div>
                    {item.jobUrl && (
                      <a href={item.jobUrl} target="_blank" rel="noopener noreferrer" className="text-[0.55rem] text-primary hover:underline flex items-center gap-1">
                        <Link className="w-3 h-3" /> View Job
                      </a>
                    )}
                  </div>
                  {item.roles && item.roles.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.roles.map((r, ri) => (
                        <Badge key={ri} variant="outline" className="text-[0.45rem] h-3.5">{r}</Badge>
                      ))}
                    </div>
                  )}
                  <div className="text-[0.6rem] text-muted-foreground">{item.reason}</div>

                  {item.recruiters && item.recruiters.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <IdentificationCard className="w-3 h-3 text-purple-500" />
                        <span className="text-[0.55rem] font-bold text-purple-500">Recruiters</span>
                      </div>
                      {item.recruiters.map((r, ri) => (
                        <a key={ri} href={r.linkedinSearch} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                          {r.title || r.name}
                        </a>
                      ))}
                    </div>
                  )}

                  {item.engineers && item.engineers.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <Gear className="w-3 h-3 text-blue-500" />
                        <span className="text-[0.55rem] font-bold text-blue-500">Engineers</span>
                      </div>
                      {item.engineers.map((e, ei) => (
                        <a key={ei} href={e.linkedinSearch} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                          {e.title || e.name}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {networking.length === 0 && (
                <div className="text-xs text-muted-foreground text-center py-4">
                  Run analysis to generate networking targets.
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-yellow-500" />
              <h3 className="font-extrabold text-sm">Networking Tips</h3>
            </div>
            <div className="space-y-2 text-[0.6rem] text-muted-foreground">
              {[
                'Search for <strong>Recruiters</strong> and <strong>Talent Acquisition</strong> at each company first.',
                'Connect with <strong>Software Engineers</strong> and <strong>Backend Engineers</strong> for referrals.',
                'Personalize your connection request — mention the specific role.',
                'Engage with their posts before connecting.',
                'Follow up 1 week after connecting.',
              ].map((tip, i) => (
                <div key={i} className="flex items-start gap-2">
                  <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                  <span dangerouslySetInnerHTML={{ __html: tip }} />
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Link className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Quick Searches</h3>
            </div>
            <div className="space-y-1.5">
              {[
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22recruiter%22+%22software+engineer%22+Berlin', label: 'Recruiters — Software Engineers Berlin' },
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22talent+acquisition%22+%22backend%22+Berlin', label: 'Talent Acquisition — Backend Berlin' },
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22hiring+manager%22+%22python%22+Berlin', label: 'Hiring Managers — Python Berlin' },
              ].map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-[0.6rem] text-primary hover:underline p-1.5 rounded hover:bg-muted transition">
                  <MagnifyingGlass className="w-3 h-3" />
                  {link.label}
                </a>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
