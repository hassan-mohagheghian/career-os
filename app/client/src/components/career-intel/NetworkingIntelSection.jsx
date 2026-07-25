import {
  Users, MagnifyingGlass, Link, ArrowSquareOut, ArrowsClockwise, Target, Clock
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

function NetworkTarget({ target }) {
  return (
    <Card className="p-3 transition hover:border-primary">
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm">{target.company}</span>
        <Badge variant="secondary" className="text-[0.45rem] h-3">Priority #{target.priority}</Badge>
      </div>
      <div className="flex flex-wrap gap-1 mb-2">
        {target.contactTypes?.map((type, i) => (
          <Badge key={i} variant="outline" className="text-[0.45rem] h-3">{type}</Badge>
        ))}
      </div>
      <div className="text-[0.6rem] text-muted-foreground mb-2">{target.reason}</div>
      {target.strategy && (
        <div className="text-[0.55rem] text-primary p-1.5 rounded bg-primary/5">
          <strong>Strategy:</strong> {target.strategy}
        </div>
      )}
      {target.linkedinSearchQueries?.length > 0 && (
        <div className="mt-2 space-y-1">
          {target.linkedinSearchQueries.map((q, i) => (
            <a key={i} href={q} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-[0.55rem] text-blue-400 hover:text-blue-300 transition">
              <ArrowSquareOut className="w-3 h-3" /> LinkedIn Search {i + 1}
            </a>
          ))}
        </div>
      )}
    </Card>
  )
}

export default function NetworkingIntelSection({ data, refreshing, onRefresh, status }) {
  const networking = data?.networking || {}
  const targets = networking.targets || []
  const strategy = networking.connectionStrategy || {}

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="font-extrabold text-sm">Networking Intelligence</h3>
          {status?.networking?.lastRun && (
            <span className="text-[0.5rem] text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />{formatTimeAgo(status.networking.lastRun)}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.networking} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.networking && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Connection Strategy */}
      {strategy.whoToContactFirst && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5 text-primary" />
            <h4 className="font-extrabold text-sm">Connection Strategy</h4>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[0.6rem] text-muted-foreground mb-1">Who to Contact First</div>
              <div className="text-xs font-bold">{strategy.whoToContactFirst}</div>
              <div className="text-[0.6rem] text-muted-foreground mt-1">{strategy.why}</div>
            </div>
            <div>
              <div className="text-[0.6rem] text-muted-foreground mb-1">Suggested Search Queries</div>
              <div className="space-y-1">
                {strategy.suggestedSearchQueries?.map((q, i) => (
                  <div key={i} className="text-[0.55rem] text-blue-400 truncate">{q}</div>
                ))}
              </div>
            </div>
          </div>
          {strategy.outreachTemplate && (
            <div className="mt-3 p-2 rounded bg-muted text-[0.6rem] text-muted-foreground">
              <strong>Outreach Template:</strong> {strategy.outreachTemplate}
            </div>
          )}
        </Card>
      )}

      {/* Network Targets */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-5 h-5 text-cyan-500" />
          <h4 className="font-extrabold text-sm">Networking Targets</h4>
          <Badge variant="secondary" className="text-[0.5rem]">{targets.length}</Badge>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {targets.length > 0 ? targets.map((t, i) => (
            <NetworkTarget key={i} target={t} />
          )) : (
            <div className="col-span-2 text-xs text-muted-foreground text-center py-4">
              No networking targets identified yet
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
