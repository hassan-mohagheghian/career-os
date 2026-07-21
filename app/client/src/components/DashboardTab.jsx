import {
  Briefcase, ChartBar, Gear, Target, Brain, Rocket, House, TrendUp,
  BookOpen, ChartLineUp, Wrench, Clipboard, Lightning, Globe, Link,
  Users, IdentificationCard, FileText, ArrowsClockwise, CheckCircle,
  MagnifyingGlass, Lightbulb, Stack, LinkedinLogo
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { CompactJobCard } from '@/components/ProcessedCards'
import { TechCard, StackCard } from '@/components/TechCards'

const EMOJI_ICON_MAP = {
  '🎯': <Target className="w-4 h-4" />, '🌍': <Globe className="w-4 h-4" />,
  '⚡': <Lightning className="w-4 h-4" />, '🏢': <Buildings className="w-4 h-4" />,
  '🚀': <Rocket className="w-4 h-4" />, '📈': <TrendUp className="w-4 h-4" />,
  '💪': <TrendUp className="w-4 h-4" />, '📚': <BookOpen className="w-4 h-4" />,
  '💡': <Lightbulb className="w-4 h-4" />, '🔍': <MagnifyingGlass className="w-4 h-4" />,
  '🧠': <Brain className="w-4 h-4" />, '⚙️': <Gear className="w-4 h-4" />,
  '🎓': <GraduationCap className="w-4 h-4" />, '💰': <CurrencyDollar className="w-4 h-4" />,
  '👥': <Users className="w-4 h-4" />, '⏳': <HourglassHigh className="w-4 h-4" />,
  '🤝': <Handshake className="w-4 h-4" />, '💼': <Briefcase className="w-4 h-4" />,
  '📊': <ChartBar className="w-4 h-4" />, '🔧': <Wrench className="w-4 h-4" />,
  '🐻': <TreePalm className="w-4 h-4" />, '🦁': <Compass className="w-4 h-4" />,
  '🎵': <MusicNote className="w-4 h-4" />, '🏛️': <Buildings className="w-4 h-4" />,
  '🏦': <Bank className="w-4 h-4" />, '🗼': <Buildings className="w-4 h-4" />,
  '🏭': <Factory className="w-4 h-4" />, '🏠': <HouseSimple className="w-4 h-4" />,
  '🇩🇪': <Globe className="w-4 h-4" />, '📍': <MapPin className="w-4 h-4" />,
  '🛂': <IdentificationCard className="w-4 h-4" />, '🐍': <Bug className="w-4 h-4" />,
  '📋': <Clipboard className="w-4 h-4" />, '🔗': <Link className="w-4 h-4" />,
}

import {
  Buildings, GraduationCap, CurrencyDollar, HourglassHigh, Handshake,
  TreePalm, Compass, MusicNote, Bank, Factory, HouseSimple, Bug, MapPin
} from '@phosphor-icons/react'

function EmojiIcon({ emoji }) {
  return EMOJI_ICON_MAP[emoji] || <span className="w-4 h-4">{emoji}</span>
}

export default function DashboardTab({ analysis, jobs, resumes, linkedinProfiles, cities, rules, dashboardSubTab, refreshing, onSetDashboardSubTab, onRefreshAnalysis, onRefreshStrategy, onRefreshNetworking, onRefreshSkillsTab, onOpenDrawer }) {
  const analysisData = analysis?.analysis || {}
  const hasAnalysis = !!analysis?.analysis
  const overview = analysisData.overview || {}
  const strategy = analysisData.strategy || []
  const strengths = analysisData.strengths || []
  const weaknesses = analysisData.weaknesses || []
  const visaCompanies = analysisData.visa_companies || []
  const applyUrgency = analysisData.apply_urgency || []
  const techStackData = analysisData.techStack || []
  const techLearningData = analysisData.techLearning || []
  const skillJobFit = analysisData.skillJobFit || []
  const learningROI = analysisData.learningROI || []
  const searchSummary = analysisData.searchSummary || {}
  const improvements = analysisData.improvements || []
  const goals = analysisData.goals || []
  const networking = analysisData.networking || []

  const highMatchJobs = jobs.filter(j => j.match === 'High')
  const applyNow = jobs.filter(j => ['A', 'A+', 'A++'].includes(j.score))
  const remoteJobs = jobs.filter(j => j.work_type === 'Remote')
  const visaReady = jobs.filter(j => j.visa === 'BEST' || j.visa === 'Strong')

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
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-extrabold">Dashboard</h2>
          <Tabs value={dashboardSubTab} onValueChange={onSetDashboardSubTab}>
            <TabsList className="bg-muted">
              <TabsTrigger value="overview"><ChartBar className="w-4 h-4 mr-1.5" />Overview</TabsTrigger>
              <TabsTrigger value="strategy"><Target className="w-4 h-4 mr-1.5" />Strategy</TabsTrigger>
              <TabsTrigger value="networking"><Users className="w-4 h-4 mr-1.5" />Networking</TabsTrigger>
              <TabsTrigger value="skills"><Brain className="w-4 h-4 mr-1.5" />Skills</TabsTrigger>
            </TabsList>
          </Tabs>
          <p className="text-xs text-muted-foreground">
            {analysis?.created_at && <span>Last updated: {new Date(analysis.created_at).toLocaleString()}</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={onRefreshAnalysis} disabled={refreshing.analysis} variant={refreshing.analysis ? "secondary" : "outline"} size="sm" className="gap-1.5">
            <ArrowsClockwise className={cn("w-3.5 h-3.5", refreshing.analysis && "animate-spin")} />
            {refreshing.analysis ? 'Updating...' : 'Refresh All'}
          </Button>
        </div>
      </div>

      {!hasAnalysis && !refreshing.analysis && (
        <Card className="p-8 text-center border-dashed">
          <ChartBar className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-sm font-semibold mb-1">No analysis data yet</p>
          <p className="text-xs text-muted-foreground mb-4">Click "Refresh Analysis" to generate insights from your {jobs.length} processed jobs.</p>
          <Button onClick={onRefreshAnalysis} size="sm" className="gap-1.5">
            <ArrowsClockwise className="w-3.5 h-3.5" /> Generate Analysis
          </Button>
        </Card>
      )}

      {dashboardSubTab === 'overview' && (
        <OverviewSubTab analysis={analysis} jobs={jobs} resumes={resumes} linkedinProfiles={linkedinProfiles} cities={cities} rules={rules} refreshing={refreshing} overview={overview} highMatchJobs={highMatchJobs} applyNow={applyNow} remoteJobs={remoteJobs} visaReady={visaReady} skillJobFit={skillJobFit} visaCompanies={visaCompanies} onRefresh={onRefreshAnalysis} onOpenDrawer={onOpenDrawer} />
      )}

      {dashboardSubTab === 'strategy' && (
        <StrategySubTab analysis={analysis} refreshing={refreshing} strategy={strategy} strengths={strengths} improvements={improvements} applyUrgency={applyUrgency} goals={goals} searchSummary={searchSummary} onRefresh={onRefreshStrategy} />
      )}

      {dashboardSubTab === 'networking' && (
        <NetworkingSubTab analysis={analysis} refreshing={refreshing} networking={networking} onRefresh={onRefreshNetworking} />
      )}

      {dashboardSubTab === 'skills' && (
        <SkillsSubTab analysis={analysis} refreshing={refreshing} techStackData={techStackData} techLearningData={techLearningData} strongStack={strongStack} midStack={midStack} weakStack={weakStack} p1Tech={p1Tech} p2Tech={p2Tech} weaknesses={weaknesses} learningROI={learningROI} avgLevel={avgLevel} onRefresh={onRefreshSkillsTab} />
      )}
    </div>
  )
}

function OverviewSubTab({ analysis, jobs, resumes, linkedinProfiles, cities, rules, refreshing, overview, highMatchJobs, applyNow, remoteJobs, visaReady, skillJobFit, visaCompanies, onRefresh, onOpenDrawer }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-extrabold text-sm">Overview</h3>
          {analysis?.created_at && <span className="text-[0.5rem] text-muted-foreground">Updated {new Date(analysis.created_at).toLocaleTimeString()}</span>}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-6 gap-3">
        {[
          { n: overview.totalJobs || jobs.length, l: 'Total Jobs', c: 'text-primary', icon: <Briefcase className="w-5 h-5" /> },
          { n: overview.highMatch || highMatchJobs.length, l: 'High Match', c: 'text-green-500', icon: <Target className="w-5 h-5" /> },
          { n: overview.applyNow || applyNow.length, l: 'Apply Now (75+)', c: 'text-yellow-500', icon: <Rocket className="w-5 h-5" /> },
          { n: overview.remoteJobs || remoteJobs.length, l: 'Remote', c: 'text-cyan-500', icon: <House className="w-5 h-5" /> },
          { n: overview.visaReady || visaReady.length, l: 'Visa Ready', c: 'text-purple-500', icon: <IdentificationCard className="w-5 h-5" /> },
          { n: resumes.filter(r => r.id !== 'original').length, l: 'Resumes', c: 'text-primary', icon: <FileText className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-4 transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-2xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.65rem] uppercase tracking-wider mt-0.5 text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Rocket className="w-5 h-5 text-yellow-500" />
              <h3 className="font-extrabold text-sm">Apply Now — Score 75+</h3>
              <Badge variant="secondary" className="text-[0.6rem] bg-green-500/15 text-green-500">{applyNow.length} jobs</Badge>
            </div>
            {applyNow.length === 0 ? <div className="text-center py-6 text-xs text-muted-foreground">No jobs scored A or above yet</div> : (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                {applyNow.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => onOpenDrawer(j.num)} />)}
              </div>
            )}
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-green-500" />
              <h3 className="font-extrabold text-sm">High Match Jobs</h3>
              <Badge variant="secondary" className="text-[0.6rem] bg-green-500/15 text-green-500">{highMatchJobs.length} jobs</Badge>
            </div>
            {highMatchJobs.length === 0 ? <div className="text-center py-6 text-xs text-muted-foreground">No high match jobs</div> : (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                {highMatchJobs.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => onOpenDrawer(j.num)} />)}
              </div>
            )}
          </Card>

          {skillJobFit.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Link className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Skill-Job Fit Analysis</h3>
              </div>
              <div className="space-y-2">
                {skillJobFit.slice(0, 8).map((item, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs p-2 rounded-lg hover:bg-muted transition">
                    <div className="w-24 font-semibold">{item.skill}</div>
                    <Progress value={item.fitScore} className="flex-1 h-2" />
                    <div className="w-12 text-right font-bold text-primary">{item.fitScore}%</div>
                    <div className="w-20 text-right text-muted-foreground">{item.jobsRequiring}/{overview.totalJobs || jobs.length}</div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Globe className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Cities</h3>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {cities?.slice(0, 6).map((c, i) => (
                <Card key={i} className="p-2 text-center transition hover:border-primary">
                  <div className="mb-0.5 text-primary"><EmojiIcon emoji={c.icon} /></div>
                  <div className="font-bold text-xs">{c.name}</div>
                  <div className="text-[0.55rem] text-muted-foreground">{c.info}</div>
                  <div className="text-[0.55rem] font-semibold text-primary">{c.jobs}</div>
                </Card>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <IdentificationCard className="w-5 h-5 text-purple-500" />
              <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
            </div>
            {visaCompanies.length > 0 ? (
              <div className="space-y-1.5">
                {visaCompanies.slice(0, 6).map((j, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{j.company}</span>
                    <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{j.visa}</Badge>
                  </div>
                ))}
              </div>
            ) : <div className="text-xs text-muted-foreground">No visa data yet</div>}
          </Card>

          {(() => {
            const latestResume = resumes.filter(r => r.id?.startsWith('original_')).sort((a, b) => (b.version || 0) - (a.version || 0))[0]
            const latestLinkedin = linkedinProfiles.filter(p => p.id?.startsWith('linkedin_')).sort((a, b) => (b.version || 0) - (a.version || 0))[0]
            if (!latestResume && !latestLinkedin) return null
            return (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-5 h-5 text-primary" />
                  <h3 className="font-extrabold text-sm">Your Profile</h3>
                </div>
                <div className="space-y-2">
                  {latestResume && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1.5"><FileText className="w-3 h-3 text-green-500" /> Resume</span>
                      <Badge variant="secondary" className="text-[0.5rem]">v{latestResume.version}</Badge>
                    </div>
                  )}
                  {latestLinkedin && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1.5"><LinkedinLogo className="w-3 h-3 text-[#0A66C2]" /> LinkedIn</span>
                      <Badge variant="secondary" className="text-[0.5rem]">v{latestLinkedin.version}</Badge>
                    </div>
                  )}
                  {!latestResume && <div className="text-[0.6rem] text-yellow-500">No resume uploaded</div>}
                </div>
              </Card>
            )
          })()}

          {rules && rules.length > 0 && (() => {
            const fitRules = rules.filter(r => r.category === 'fit' && r.enabled)
            const successRules = rules.filter(r => r.category === 'success' && r.enabled)
            if (fitRules.length === 0 && successRules.length === 0) return null
            return (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Gear className="w-5 h-5 text-primary" />
                  <h3 className="font-extrabold text-sm">Scoring Rules</h3>
                  <Badge variant="secondary" className="text-[0.5rem]">{fitRules.length + successRules.length} active</Badge>
                </div>
                <div className="space-y-2">
                  <div>
                    <div className="text-[0.6rem] text-muted-foreground mb-1">Fit Rules ({fitRules.length})</div>
                    <div className="space-y-0.5">
                      {fitRules.slice(0, 4).map((r, i) => (
                        <div key={i} className="text-[0.6rem] text-muted-foreground truncate" title={r.value}>
                          <span className="font-semibold text-foreground/70">#{r.priority}</span> {r.key}
                        </div>
                      ))}
                      {fitRules.length > 4 && <div className="text-[0.55rem] text-muted-foreground/60">+{fitRules.length - 4} more</div>}
                    </div>
                  </div>
                  <div>
                    <div className="text-[0.6rem] text-muted-foreground mb-1">Success Rules ({successRules.length})</div>
                    <div className="space-y-0.5">
                      {successRules.slice(0, 4).map((r, i) => (
                        <div key={i} className="text-[0.6rem] text-muted-foreground truncate" title={r.value}>
                          <span className="font-semibold text-foreground/70">#{r.priority}</span> {r.key}
                        </div>
                      ))}
                      {successRules.length > 4 && <div className="text-[0.55rem] text-muted-foreground/60">+{successRules.length - 4} more</div>}
                    </div>
                  </div>
                </div>
              </Card>
            )
          })()}
        </div>
      </div>
    </div>
  )
}

function StrategySubTab({ analysis, refreshing, strategy, strengths, improvements, applyUrgency, goals, searchSummary, onRefresh }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-extrabold text-sm">Strategy</h3>
          {analysis?.created_at && <span className="text-[0.5rem] text-muted-foreground">Updated {new Date(analysis.created_at).toLocaleTimeString()}</span>}
        </div>
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
              {strategy.length === 0 && improvements.length === 0 && <Badge variant="secondary" className="text-[0.55rem]">Processing...</Badge>}
            </div>
            <div className="space-y-2">
              {strategy.map((g, i) => (
                <div key={`s-${i}`} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-muted border-l-2 border-primary">
                  <span className="shrink-0 text-primary"><EmojiIcon emoji={g.icon} /></span>
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
                {searchSummary.avgApplicants > 0 && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Avg Applicants</span>
                    <span className="font-bold">{Math.round(searchSummary.avgApplicants)}</span>
                  </div>
                )}
                {searchSummary.dateRange && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Date Range</span>
                    <span className="font-bold text-[0.6rem]">{searchSummary.dateRange}</span>
                  </div>
                )}
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
                {searchSummary.topRoles?.length > 0 && (
                  <div className="mt-1.5">
                    <div className="text-[0.6rem] text-muted-foreground mb-1">Top Roles</div>
                    <div className="flex flex-wrap gap-1">
                      {searchSummary.topRoles.slice(0, 5).map((r, i) => (
                        <Badge key={i} variant="secondary" className="text-[0.5rem]">{r}</Badge>
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

function NetworkingSubTab({ analysis, refreshing, networking, onRefresh }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-extrabold text-sm">Networking</h3>
          {analysis?.created_at && <span className="text-[0.5rem] text-muted-foreground">Updated {new Date(analysis.created_at).toLocaleTimeString()}</span>}
        </div>
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
              {networking.length === 0 && <Badge variant="secondary" className="text-[0.55rem]">Processing...</Badge>}
            </div>
            <p className="text-[0.6rem] text-muted-foreground mb-3">Top companies to connect with on LinkedIn. Reach out to recruiters and engineering staff to increase your visibility.</p>
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
                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                        item.match === 'High' ? "bg-green-500/15 text-green-500" :
                        item.match === 'Medium' ? "bg-yellow-500/15 text-yellow-500" :
                        "bg-gray-500/15 text-gray-500"
                      )}>{item.match}</Badge>
                    </div>
                    {item.jobUrl && (
                      <a href={item.jobUrl} target="_blank" rel="noopener noreferrer" className="text-[0.55rem] text-primary hover:underline flex items-center gap-1">
                        <Link className="w-3 h-3" /> View Job
                      </a>
                    )}
                    {item.company_url && (
                      <a href={item.company_url} target="_blank" rel="noopener noreferrer" className="text-[0.55rem] text-muted-foreground hover:text-primary hover:underline flex items-center gap-1">
                        <Globe className="w-3 h-3" /> Website
                      </a>
                    )}
                    {item.linkedin_url && (
                      <a href={item.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-[0.55rem] text-muted-foreground hover:text-primary hover:underline flex items-center gap-1">
                        <LinkedinLogo className="w-3 h-3" /> LinkedIn
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
                        <span className="text-[0.55rem] font-bold text-purple-500">Recruiters & Talent</span>
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
                        <span className="text-[0.55rem] font-bold text-blue-500">Software Engineers</span>
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
              {networking.length === 0 && !refreshing.analysis && (
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
                'Search for <strong>Recruiters</strong> and <strong>Talent Acquisition</strong> at each company first — they control the hiring pipeline.',
                'Connect with <strong>Software Engineers</strong> and <strong>Backend Engineers</strong> — they can refer you internally and share team culture.',
                'Personalize your connection request — mention the specific role and why you\'re interested in their company.',
                'Engage with their posts before connecting — like, comment, and share to build familiarity.',
                'Follow up 1 week after connecting with a brief message about your interest in the role.',
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
              <LinkedinLogo className="w-5 h-5 text-[#0A66C2]" />
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

function SkillsSubTab({ analysis, refreshing, techStackData, techLearningData, strongStack, midStack, weakStack, p1Tech, p2Tech, weaknesses, learningROI, avgLevel, onRefresh }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-extrabold text-sm">Skills</h3>
          {analysis?.created_at && <span className="text-[0.5rem] text-muted-foreground">Updated {new Date(analysis.created_at).toLocaleTimeString()}</span>}
        </div>
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
              {weaknesses.filter(w => !p1Tech.some(p => p.name === w.name) && !p2Tech.some(p => p.name === w.name)).map((t, i) => (
                <div key={`w-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.detail}</span>
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
