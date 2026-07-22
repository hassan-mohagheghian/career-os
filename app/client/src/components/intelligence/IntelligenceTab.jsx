import {
  ChartBar, Target, Brain, Rocket, Buildings, Users, ArrowsClockwise, Clock
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import MarketSection from './MarketSection'
import OpportunitySection from './OpportunitySection'
import StrategySection from './StrategySection'
import SkillsSection from './SkillsSection'
import CompanySection from './CompanySection'
import NetworkingSection from './NetworkingSection'

function formatTimestamp(ts) {
  if (!ts) return null
  const date = new Date(ts)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function SectionTimestamp({ label, timestamp, isRefreshing }) {
  const formatted = formatTimestamp(timestamp)
  return (
    <span className="flex items-center gap-1 text-[0.6rem] text-muted-foreground">
      <Clock className="w-2.5 h-2.5" />
      {isRefreshing ? (
        <span className="text-primary">Updating...</span>
      ) : formatted ? (
        <span>{label}: {formatted}</span>
      ) : (
        <span>{label}: Never</span>
      )}
    </span>
  )
}

export default function IntelligenceTab({ analysis, timestamps, getLastUpdated, jobs, resumes, linkedinProfiles, cities, rules, intelligenceSubTab, refreshing, onSetIntelligenceSubTab, onRefreshAll, onRefreshMarket, onRefreshOpportunity, onRefreshStrategy, onRefreshNetworking, onRefreshSkills, onOpenDrawer }) {
  const hasAnalysis = !!analysis?.analysis
  const analysisData = analysis?.analysis || {}
  const overallTimestamp = analysis?.created_at || getLastUpdated?.('all')

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
          <SectionTimestamp
            label={intelligenceSubTab === 'all' ? 'All' : intelligenceSubTab}
            timestamp={getLastUpdated?.(intelligenceSubTab) || overallTimestamp}
            isRefreshing={refreshing[intelligenceSubTab] || refreshing.all}
          />
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={onRefreshAll} disabled={refreshing.all} variant={refreshing.all ? "secondary" : "outline"} size="sm" className="gap-1.5">
            <ArrowsClockwise className={cn("w-3.5 h-3.5", refreshing.all && "animate-spin")} />
            {refreshing.all ? 'Updating...' : 'Refresh All'}
          </Button>
        </div>
      </div>

      {!hasAnalysis && !refreshing.all && (
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
        <MarketSection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshMarket} onOpenDrawer={onOpenDrawer} lastUpdated={getLastUpdated?.('market')} />
      )}

      {intelligenceSubTab === 'opportunity' && (
        <OpportunitySection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshOpportunity} onOpenDrawer={onOpenDrawer} lastUpdated={getLastUpdated?.('opportunity')} />
      )}

      {intelligenceSubTab === 'strategy' && (
        <StrategySection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshStrategy} lastUpdated={getLastUpdated?.('strategy')} />
      )}

      {intelligenceSubTab === 'skills' && (
        <SkillsSection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshSkills} lastUpdated={getLastUpdated?.('skills')} />
      )}

      {intelligenceSubTab === 'company' && (
        <CompanySection analysis={analysisData} jobs={jobs} refreshing={refreshing} onRefresh={onRefreshAll} onOpenDrawer={onOpenDrawer} lastUpdated={getLastUpdated?.('all')} />
      )}

      {intelligenceSubTab === 'networking' && (
        <NetworkingSection analysis={analysisData} refreshing={refreshing} onRefresh={onRefreshNetworking} lastUpdated={getLastUpdated?.('networking')} />
      )}
    </div>
  )
}
