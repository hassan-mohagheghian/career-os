import {
  Globe, MapPin, House, IdentificationCard, Lightbulb, ArrowsClockwise, Clock
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

function formatTimeAgo(ts) {
  if (!ts) return ''
  const diffMs = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return days < 7 ? `${days}d ago` : new Date(ts).toLocaleDateString()
}

export default function MarketIntelSection({ data, refreshing, onRefresh, status }) {
  const market = data?.market || {}
  const countries = market.countries || []
  const cities = market.cities || []
  const remote = market.remoteOpportunities || {}
  const visa = market.visaFriendliness || []
  const insights = market.insights || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="font-extrabold text-sm">Market Intelligence</h3>
          {status?.market?.lastRun && (
            <span className="text-[0.5rem] text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />{formatTimeAgo(status.market.lastRun)}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.market} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.market && "animate-spin")} /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-[1fr_260px] gap-4">
        <div className="space-y-4">
          {/* Cities */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-5 h-5 text-primary" />
              <h4 className="font-extrabold text-sm">Cities</h4>
            </div>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {cities.map((city, i) => (
                <div key={i} className="p-2 rounded-lg border border-muted hover:border-primary transition">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs">{city.name}</span>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3",
                      city.opportunityLevel === 'high' ? 'bg-green-500/15 text-green-500' :
                      city.opportunityLevel === 'medium' ? 'bg-yellow-500/15 text-yellow-500' : 'bg-gray-500/15 text-gray-400'
                    )}>{city.opportunityLevel}</Badge>
                  </div>
                  <div className="text-[0.55rem] text-muted-foreground mt-0.5">{city.jobCount} jobs</div>
                  {city.topCompanies?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {city.topCompanies.slice(0, 3).map((co, j) => (
                        <Badge key={j} variant="secondary" className="text-[0.45rem]">{co}</Badge>
                      ))}
                    </div>
                  )}
                  {city.insight && <div className="text-[0.55rem] text-primary mt-1">{city.insight}</div>}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          {/* Countries */}
          {countries.length > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-4 h-4 text-primary" />
                <h4 className="font-extrabold text-xs">Countries</h4>
              </div>
              <div className="space-y-1.5">
                {countries.map((c, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <div className="w-16 text-[0.55rem] text-muted-foreground truncate">{c.name}</div>
                    <div className="flex-1 h-3.5 bg-muted rounded overflow-hidden">
                      <div className="h-full bg-primary/60 rounded flex items-center px-1" style={{ width: `${Math.max(c.percentage || 5, 5)}%` }}>
                        <span className="text-[0.45rem] font-bold text-white">{c.jobCount}</span>
                      </div>
                    </div>
                    <div className="w-8 text-right text-[0.5rem] font-bold text-primary">{Math.round(c.percentage || 0)}%</div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Remote Opportunities */}
          {remote.count > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <House className="w-4 h-4 text-cyan-500" />
                <h4 className="font-extrabold text-xs">Remote</h4>
              </div>
              <div className="text-center mb-2">
                <div className="text-xl font-extrabold text-cyan-500">{remote.count}</div>
                <div className="text-[0.5rem] text-muted-foreground">{Math.round(remote.percentage || 0)}% of all jobs</div>
              </div>
              {remote.topCompanies?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {remote.topCompanies.slice(0, 4).map((co, i) => (
                    <Badge key={i} variant="secondary" className="text-[0.4rem]">{co}</Badge>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* Visa Friendliness */}
          {visa.length > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <IdentificationCard className="w-4 h-4 text-purple-500" />
                <h4 className="font-extrabold text-xs">Visa</h4>
              </div>
              <div className="space-y-1.5">
                {visa.map((v, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[0.55rem]">
                    <span className="font-semibold w-14 truncate">{v.country}</span>
                    <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 shrink-0",
                      v.rating === 'excellent' ? 'bg-green-500/15 text-green-500' :
                      v.rating === 'good' ? 'bg-blue-500/15 text-blue-500' :
                      v.rating === 'moderate' ? 'bg-yellow-500/15 text-yellow-500' : 'bg-red-500/15 text-red-500'
                    )}>{v.rating}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Insights */}
          {insights.length > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-yellow-500" />
                <h4 className="font-extrabold text-xs">Insights</h4>
              </div>
              <div className="space-y-1.5">
                {insights.map((insight, i) => (
                  <div key={i} className="p-1.5 rounded border border-yellow-500/20 bg-yellow-500/5">
                    <div className="text-[0.5rem] text-muted-foreground">{insight.observation}</div>
                    {insight.action && <div className="text-[0.45rem] text-primary mt-0.5">{insight.action}</div>}
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
