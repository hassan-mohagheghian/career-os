import { useState, useEffect, useCallback, useRef } from 'react'
import { List, Clock, Warning, CheckCircle, Spinner, X, Briefcase, Buildings, Brain, TreeStructure, Lightbulb } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'

const API = '/api'
const PAGE_SIZE = 30

const SOURCE_CONFIG = {
  'career-intel': { icon: Lightbulb, color: 'bg-amber-500/15 text-amber-500', label: 'Intel' },
  'roadmap': { icon: TreeStructure, color: 'bg-emerald-500/15 text-emerald-500', label: 'Roadmap' },
  'job-processing': { icon: Briefcase, color: 'bg-blue-500/15 text-blue-500', label: 'Job' },
  'company-processing': { icon: Buildings, color: 'bg-purple-500/15 text-purple-500', label: 'Company' },
}

function formatTimeAgo(ts) {
  if (!ts) return ''
  const diffMs = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(ts).toLocaleDateString()
}

function HistoryItem({ item }) {
  const cfg = SOURCE_CONFIG[item.source] || SOURCE_CONFIG['career-intel']
  const Icon = cfg.icon
  const statusColor = item.status === 'completed' ? 'bg-green-500' :
    item.status === 'failed' ? 'bg-red-500' :
    item.status === 'cancelled' ? 'bg-yellow-500' :
    item.status === 'processing' || item.status === 'running' ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'

  return (
    <div className="flex items-start gap-2 p-2 rounded hover:bg-muted transition text-xs">
      <div className={cn("w-2.5 h-2.5 rounded-full shrink-0 mt-1", statusColor)} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold truncate">{item.title}</span>
          <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 shrink-0", cfg.color)}>
            {cfg.label}
          </Badge>
          <span className={cn("font-semibold text-[0.55rem] shrink-0",
            item.status === 'completed' ? "text-green-500" :
            item.status === 'failed' ? "text-red-500" :
            item.status === 'cancelled' ? "text-yellow-500" : "text-muted-foreground"
          )}>{item.status}</span>
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-muted-foreground text-[0.55rem] flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5" />
            {formatTimeAgo(item.completed_at || item.started_at)}
          </span>
          {item.session_id && (
            <span className="text-muted-foreground/50 text-[0.5rem] font-mono truncate max-w-[100px]" title={item.session_id}>
              {item.session_id}
            </span>
          )}
        </div>
        {item.error && (
          <div className="text-red-500 text-[0.55rem] mt-0.5 flex items-center gap-1">
            <Warning className="w-2.5 h-2.5 shrink-0" />
            <span className="truncate">{item.error}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function GenerationHistoryDrawer({ open, onOpenChange }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [loadedCount, setLoadedCount] = useState(0)
  const scrollRef = useRef(null)
  const loadingRef = useRef(false)

  const fetchHistory = useCallback((offset = 0, append = false) => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    fetch(`${API}/gallery/generation-history?limit=${PAGE_SIZE}&offset=${offset}`)
      .then(r => r.ok ? r.json() : { items: [], total: 0 })
      .then(d => {
        const newItems = d.items || []
        const newTotal = d.total || 0
        setTotal(newTotal)
        setItems(prev => append ? [...prev, ...newItems] : newItems)
        setLoadedCount(append ? loadedCount + newItems.length : newItems.length)
      })
      .catch(() => { if (!append) setItems([]) })
      .finally(() => { setLoading(false); loadingRef.current = false })
  }, [loadedCount])

  useEffect(() => {
    if (open) {
      fetchHistory()
    }
  }, [open, fetchHistory])

  const handleScroll = useCallback(() => {
    const node = scrollRef.current
    if (!node || loadingRef.current || loadedCount >= total) return
    if (node.scrollTop + node.clientHeight >= node.scrollHeight - 100) {
      fetchHistory(loadedCount, true)
    }
  }, [loadedCount, total, fetchHistory])

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[380px] sm:w-[440px] p-0">
        <SheetHeader className="p-5 pb-3">
          <SheetTitle className="flex items-center gap-2">
            <List className="w-5 h-5" />
            Generation History
          </SheetTitle>
          <SheetDescription>
            {total} total runs across all systems
          </SheetDescription>
        </SheetHeader>
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="px-5 pb-5 space-y-0.5 overflow-y-auto h-[calc(100vh-120px)]"
        >
          {items.map((item, i) => (
            <HistoryItem key={`${item.source}-${item.id}-${i}`} item={item} />
          ))}
          {items.length === 0 && !loading && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No generation history yet
            </div>
          )}
          {loading && (
            <div className="text-center py-2 text-muted-foreground text-[0.6rem] flex items-center justify-center gap-1">
              <Spinner className="w-3 h-3 animate-spin" /> Loading...
            </div>
          )}
          {!loading && loadedCount < total && items.length > 0 && (
            <div className="text-center py-2 text-muted-foreground text-[0.6rem]">
              Scroll for more...
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
