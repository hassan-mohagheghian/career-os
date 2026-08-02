import { Clock, Warning } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'
import { toast } from 'sonner'
import { formatTimeAgo } from '@/shared/lib/formatTimeAgo'
import { SOURCE_CONFIG, PROVIDER_LABELS, type HistoryItemData } from '@/shared/lib/sourceConfig'

export type { HistoryItemData }

function StatusDot({ status }: { status: string }) {
  const color = status === 'processed' ? 'bg-green-500' :
    status === 'failed' ? 'bg-red-500' :
    status === 'cancelled' ? 'bg-yellow-500' :
    status === 'processing' || status === 'running' ? 'bg-blue-500 animate-pulse' :
    'bg-gray-400'
  return <div className={cn("w-2.5 h-2.5 rounded-full shrink-0 mt-1", color)} />
}

function StatusText({ status }: { status: string }) {
  return (
    <span className={cn("font-semibold text-2xs shrink-0",
      status === 'processed' ? "text-green-500" :
      status === 'failed' ? "text-red-500" :
      status === 'cancelled' ? "text-yellow-500" : "text-muted-foreground"
    )}>{status}</span>
  )
}

function SessionButton({ session_id, provider }: { session_id: string | null; provider?: string | null }) {
  if (!provider) return null
  return (
    <button
      className="flex items-center gap-1 text-3xs h-2.5 shrink-0 bg-muted/50 hover:bg-muted rounded px-1 transition cursor-pointer border border-transparent hover:border-border font-mono"
      onClick={() => {
        if (session_id) {
          navigator.clipboard.writeText(session_id)
          toast.success('Session ID copied')
        }
      }}
      title={session_id ? `Click to copy: ${session_id}` : ''}
    >
      <span className="text-muted-foreground">{PROVIDER_LABELS[provider] || provider}</span>
      {session_id && (
        <span className="text-foreground">({session_id})</span>
      )}
    </button>
  )
}

function TimeInfo({ item, showFullDatetime = false }: { item: HistoryItemData; showFullDatetime?: boolean }) {
  const duration = (item as any).duration_seconds ||
    (item.started_at && item.completed_at
      ? Math.round((new Date(item.completed_at).getTime() - new Date(item.started_at).getTime()) / 1000)
      : null)
  const durationStr = duration !== null
    ? duration < 60 ? `${duration}s` : `${Math.floor(duration / 60)}m ${duration % 60}s`
    : null

  const fmtTime = (ts: string) => showFullDatetime
    ? new Date(ts).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
      {item.started_at && (
        <span className="text-muted-foreground text-2xs flex items-center gap-0.5" title={`Started: ${new Date(item.started_at).toLocaleString()}`}>
          <Clock className="w-2.5 h-2.5" />
          {fmtTime(item.started_at)}
        </span>
      )}
      {item.completed_at && (
        <span className="text-muted-foreground text-2xs flex items-center gap-0.5" title={`Ended: ${new Date(item.completed_at).toLocaleString()}`}>
          → {fmtTime(item.completed_at)}
        </span>
      )}
      {durationStr && (
        <span className="text-muted-foreground/60 text-2xs">({durationStr})</span>
      )}
      {!item.started_at && !item.completed_at && (
        <span className="text-muted-foreground text-2xs flex items-center gap-0.5">
          <Clock className="w-2.5 h-2.5" />
          {formatTimeAgo(null)}
        </span>
      )}
    </div>
  )
}

interface GenerationHistoryItemProps {
  item: HistoryItemData
  compact?: boolean
  showFullDatetime?: boolean
}

export default function GenerationHistoryItem({ item, compact = false, showFullDatetime = false }: GenerationHistoryItemProps) {
  const cfg = SOURCE_CONFIG[item.source] || SOURCE_CONFIG['job-processing']

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1.5 px-2 rounded bg-muted/40 text-2xs">
        <StatusDot status={item.status} />
        <span className="truncate flex-1">{item.title}</span>
        <Badge variant="secondary" className={cn("text-3xs h-2.5 shrink-0", cfg.color)}>
          {cfg.label}
        </Badge>
        <StatusText status={item.status} />
        <span className="text-muted-foreground">{item.started_at?.slice(0, 10)}</span>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2 p-2 rounded hover:bg-muted transition text-xs">
      <StatusDot status={item.status} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-semibold truncate">{item.title}</span>
          <Badge variant="secondary" className={cn("text-3xs h-2.5 shrink-0", cfg.color)}>
            {cfg.label}
          </Badge>
          <StatusText status={item.status} />
          <SessionButton session_id={item.session_id} provider={item.provider} />
        </div>
        <TimeInfo item={item} showFullDatetime={showFullDatetime} />
        {item.error && (
          <div className="text-red-500 text-2xs mt-0.5 flex items-center gap-1">
            <Warning className="w-2.5 h-2.5 shrink-0" />
            <span className="truncate">{item.error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
