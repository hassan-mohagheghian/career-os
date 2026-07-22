import {
  TrendUp, Target, Lightning, Lightbulb, Clipboard, MagnifyingGlass,
  ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function StrategySection({ analysis, refreshing, onRefresh }) {
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
