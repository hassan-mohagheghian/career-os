import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { List, Spinner, Funnel } from '@phosphor-icons/react'
import { AppDrawer } from './DrawerComponents'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import GenerationHistoryItem from './GenerationHistoryItem'
import { SOURCE_CONFIG, type HistoryItemData } from '@/shared/lib/sourceConfig'

const API = '/api'
const PAGE_SIZE = 100

const FILTER_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'job-processing', label: 'Job' },
  { value: 'company-processing', label: 'Company' },
  { value: 'generation:resume', label: 'Resume' },
  { value: 'generation:cover', label: 'Cover Letter' },
  { value: 'generation', label: 'All Generation' },
  { value: 'insights', label: 'Insights' },
  { value: 'roadmap', label: 'Roadmap' },
]

function matchesFilter(item: HistoryItemData, filter: string): boolean {
  if (filter === 'all') return true
  if (filter === 'generation:resume') return item.source === 'generation' && item.title === 'Resume'
  if (filter === 'generation:cover') return item.source === 'generation' && item.title === 'Cover Letter'
  if (filter === 'generation') return item.source === 'generation'
  return item.source === filter
}

interface GenerationHistoryDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function GenerationHistoryDrawer({ open, onOpenChange }: GenerationHistoryDrawerProps) {
  const [items, setItems] = useState<HistoryItemData[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [loadedCount, setLoadedCount] = useState(0)
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc')
  const [filter, setFilter] = useState('all')
  const scrollRef = useRef<HTMLDivElement>(null)
  const loadingRef = useRef(false)
  const loadedCountRef = useRef(0)

  const fetchHistory = useCallback((offset: number = 0, append: boolean = false) => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    fetch(`${API}/generation-history?limit=${PAGE_SIZE}&offset=${offset}`)
      .then(r => r.ok ? r.json() : { items: [], total: 0 })
      .then(d => {
        const newItems: HistoryItemData[] = d.items || []
        const newTotal: number = d.total || 0
        setTotal(newTotal)
        setItems(prev => append ? [...prev, ...newItems] : newItems)
        const newCount = append ? loadedCountRef.current + newItems.length : newItems.length
        loadedCountRef.current = newCount
        setLoadedCount(newCount)
      })
      .catch(() => { if (!append) setItems([]) })
      .finally(() => { setLoading(false); loadingRef.current = false })
  }, [])

  useEffect(() => {
    if (open) {
      loadedCountRef.current = 0
      setLoadedCount(0)
      fetchHistory()
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleScroll = useCallback(() => {
    const node = scrollRef.current
    if (!node || loadingRef.current || loadedCountRef.current >= total) return
    if (node.scrollTop + node.clientHeight >= node.scrollHeight - 100) {
      fetchHistory(loadedCountRef.current, true)
    }
  }, [total, fetchHistory])

  const sortedAndFiltered = useMemo(() => {
    const filtered = items.filter(item => matchesFilter(item, filter))
    const sorted = [...filtered].sort((a, b) => {
      const aTime = a.started_at || a.completed_at || ''
      const bTime = b.started_at || b.completed_at || ''
      return sortDir === 'desc' ? bTime.localeCompare(aTime) : aTime.localeCompare(bTime)
    })
    return sorted
  }, [items, filter, sortDir])

  return (
    <AppDrawer
      open={open}
      onOpenChange={onOpenChange}
    >
      <div className="p-6 pb-3">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <List className="w-5 h-5" />
          Generation History
        </div>
        <div className="text-sm text-muted-foreground">
          {sortedAndFiltered.length}{filter !== 'all' ? ` of ${total}` : ''} runs
        </div>
      </div>

      {/* Sort + Filter controls */}
      <div className="px-5 pb-3 flex items-center gap-2">
        <Select value={sortDir} onValueChange={(v) => setSortDir(v as 'desc' | 'asc')}>
          <SelectTrigger className="h-7 text-2xs w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">Newest first</SelectItem>
            <SelectItem value="asc">Oldest first</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="h-7 text-2xs w-[140px]">
            <Funnel className="w-2.5 h-2.5 mr-1 opacity-50" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {FILTER_OPTIONS.map(opt => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {filter !== 'all' && (
          <Badge variant="secondary" className="text-2xs h-5 gap-1 cursor-pointer" onClick={() => setFilter('all')}>
            Clear
          </Badge>
        )}
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="px-5 pb-5 space-y-0.5 flex-1 overflow-y-auto"
      >
        {sortedAndFiltered.map((item, i) => (
          <GenerationHistoryItem key={`${item.source}-${item.id}-${i}`} item={item} showFullDatetime />
        ))}
        {sortedAndFiltered.length === 0 && !loading && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            {filter !== 'all' ? 'No matching history' : 'No generation history yet'}
          </div>
        )}
        {loading && (
          <div className="text-center py-2 text-muted-foreground text-2xs flex items-center justify-center gap-1">
            <Spinner className="w-3 h-3 animate-spin" /> Loading...
          </div>
        )}
        {!loading && loadedCount < total && items.length > 0 && (
          <div className="text-center py-2 text-muted-foreground text-2xs">
            Scroll for more...
          </div>
        )}
      </div>
    </AppDrawer>
  )
}
