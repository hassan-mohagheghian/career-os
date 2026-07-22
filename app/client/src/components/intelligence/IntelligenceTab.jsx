import {
  ChartBar, Target, Brain, Rocket, Buildings, Users, ArrowsClockwise
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

export default function IntelligenceTab({ analysis, jobs, resumes, linkedinProfiles, cities, rules, intelligenceSubTab, refreshing, onSetIntelligenceSubTab, onRefreshAll, onRefreshMarket, onRefreshOpportunity, onRefreshStrategy, onRefreshNetworking, onRefreshSkills, onOpenDrawer }) {
  const hasAnalysis = !!analysis?.analysis
  const analysisData = analysis?.analysis || {}

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
