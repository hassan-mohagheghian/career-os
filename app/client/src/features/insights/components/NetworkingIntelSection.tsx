import {
  Users, MagnifyingGlass, Link, ArrowSquareOut, ArrowsClockwise, Target, Clock
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { formatTimeAgo } from '@/shared/lib/formatTimeAgo'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import { STEP_CONFIGS } from '@/shared/components/GenerationProgressCard'

function NetworkTarget({ target }) {
  return (
    <Card className="p-3 transition hover:border-primary">
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm">{target.company}</span>
        <Badge variant="secondary" className="text-2xs h-3">Priority #{target.priority}</Badge>
      </div>
      <div className="flex flex-wrap gap-1 mb-2">
        {target.contactTypes?.map((type, i) => (
          <Badge key={i} variant="outline" className="text-2xs h-3">{type}</Badge>
        ))}
      </div>
      <div className="text-2xs text-muted-foreground mb-2">{target.reason}</div>
      {target.strategy && (
        <div className="text-2xs text-primary p-1.5 rounded bg-primary/5">
          <strong>Strategy:</strong> {target.strategy}
        </div>
      )}
      {target.linkedinSearchQueries?.length > 0 && (
        <div className="mt-2 space-y-1">
          {target.linkedinSearchQueries.map((q, i) => (
            <a key={i} href={q} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-2xs text-blue-400 hover:text-blue-300 transition">
              <ArrowSquareOut className="w-3 h-3" /> LinkedIn Search {i + 1}
            </a>
          ))}
        </div>
      )}
    </Card>
  )
}

export default function NetworkingIntelSection({ data, refreshing, onRefresh, status, localHistory = [], singleRunning, onCancel }) {
  const networking = data?.networking || {}
  const targets = networking.targets || []
  const strategy = networking.connectionStrategy || {}

  return (
    <div className="space-y-5">
      {singleRunning && (
        <GenerationProgressCard
          title={singleRunning.title}
          type={singleRunning.source}
          progress={{ running: true, status: singleRunning.status, step: (singleRunning as any).step }}
          steps={STEP_CONFIGS['insights']?.steps}
          onCancel={onCancel}
        />
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="font-extrabold text-sm">Networking Intelligence</h3>
          {status?.networking?.lastRun && (
            <span className="text-2xs text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />{formatTimeAgo(status.networking.lastRun)}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.networking} className="gap-1 h-6 text-2xs">
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
              <div className="text-2xs text-muted-foreground mb-1">Who to Contact First</div>
              <div className="text-xs font-bold">{strategy.whoToContactFirst}</div>
              <div className="text-2xs text-muted-foreground mt-1">{strategy.why}</div>
            </div>
            <div>
              <div className="text-2xs text-muted-foreground mb-1">Suggested Search Queries</div>
              <div className="space-y-1">
                {strategy.suggestedSearchQueries?.map((q, i) => (
                  <div key={i} className="text-2xs text-blue-400 truncate">{q}</div>
                ))}
              </div>
            </div>
          </div>
          {strategy.outreachTemplate && (
            <div className="mt-3 p-2 rounded bg-muted text-2xs text-muted-foreground">
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
          <Badge variant="secondary" className="text-2xs">{targets.length}</Badge>
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

      {localHistory.length > 0 && (
        <div className="space-y-0.5 border-t border-border pt-3">
          <p className="text-2xs font-semibold text-muted-foreground">Generation History</p>
          {localHistory.map(h => (
            <GenerationHistoryItem key={`${h.source}-${h.id}`} item={h} compact />
          ))}
        </div>
      )}
    </div>
  )
}
