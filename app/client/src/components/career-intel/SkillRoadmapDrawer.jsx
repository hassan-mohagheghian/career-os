import { useState, useEffect, useCallback, useRef } from 'react'
import {
  CaretRight, CaretDown, Check, Spinner, ArrowsClockwise, TreeStructure, Lightning, X
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { Checkbox } from '@/components/ui/checkbox'

const API = '/api'

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

function getAllChildIds(topic) {
  const ids = []
  if (topic.children) {
    for (const child of topic.children) {
      ids.push(child.id)
      ids.push(...getAllChildIds(child))
    }
  }
  return ids
}

function TopicNode({ topic, checked, onToggle, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasChildren = topic.children && topic.children.length > 0
  const isComplete = checked[topic.id] === 1

  const handleToggle = () => {
    const newVal = isComplete ? 0 : 1
    if (hasChildren) {
      // Tick or untick ALL children when toggling parent
      const childIds = getAllChildIds(topic)
      onToggle(topic.id, newVal, childIds)
    } else {
      onToggle(topic.id, newVal, [])
    }
  }

  return (
    <div className={cn("select-none", depth > 0 && "ml-4")}>
      <div className={cn(
        "flex items-start gap-2 py-1.5 px-2 rounded hover:bg-muted/50 transition group",
        isComplete && "bg-green-500/5"
      )}>
        <button
          className="mt-0.5 shrink-0 w-4 h-4 flex items-center justify-center"
          onClick={() => hasChildren && setExpanded(!expanded)}
        >
          {hasChildren ? (
            expanded ? <CaretDown className="w-3 h-3 text-muted-foreground" /> : <CaretRight className="w-3 h-3 text-muted-foreground" />
          ) : (
            <span className="w-3 h-3" />
          )}
        </button>
        <Checkbox
          checked={isComplete}
          onCheckedChange={handleToggle}
          className="mt-0.5 shrink-0"
        />
        <div className="flex-1 min-w-0">
          <div className={cn(
            "text-xs font-semibold leading-tight",
            isComplete && "line-through text-muted-foreground"
          )}>
            {topic.title}
          </div>
          {topic.description && (
            <div className="text-[0.6rem] text-muted-foreground mt-0.5 leading-snug">
              {topic.description}
            </div>
          )}
        </div>
      </div>
      {hasChildren && expanded && (
        <div>
          {topic.children.map(child => (
            <TopicNode key={child.id} topic={child} checked={checked} onToggle={onToggle} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function countLeafTopics(topics) {
  let total = 0
  for (const t of topics) {
    if (!t.children || t.children.length === 0) {
      total += 1
    } else {
      total += countLeafTopics(t.children)
    }
  }
  return total
}

function countCheckedLeaves(topics, checked) {
  let total = 0
  for (const t of topics) {
    if (!t.children || t.children.length === 0) {
      if (checked[t.id] === 1) total += 1
    } else {
      total += countCheckedLeaves(t.children, checked)
    }
  }
  return total
}

export default function SkillTopicDrawer({ skillName, open, onOpenChange, onRefreshProgress }) {
  const [topics, setTopics] = useState([])
  const [checked, setChecked] = useState({})
  const [version, setVersion] = useState(0)
  const [updatedAt, setUpdatedAt] = useState(null)
  const [loading, setLoading] = useState(false)
  const [genProgress, setGenProgress] = useState(null)
  const pollRef = useRef(null)

  const fetchTopics = useCallback(async () => {
    if (!skillName || !open) return
    setLoading(true)
    try {
      const [topicsRes, progressRes] = await Promise.all([
        fetch(`${API}/skill-roadmaps?skill=${encodeURIComponent(skillName)}`),
        fetch(`${API}/skill-roadmap-progress?skill=${encodeURIComponent(skillName)}`)
      ])
      const topicsData = await topicsRes.json()
      const progressData = await progressRes.json()
      setTopics(topicsData.topics || [])
      setVersion(topicsData.version || 0)
      setUpdatedAt(topicsData.updated_at || null)
      setChecked(progressData || {})
    } catch {
      setTopics([])
      setChecked({})
    } finally {
      setLoading(false)
    }
  }, [skillName, open])

  const fetchGenProgress = useCallback(async () => {
    if (!skillName) return
    try {
      const res = await fetch(`${API}/skill-roadmaps/progress?skill=${encodeURIComponent(skillName)}`)
      const data = await res.json()
      setGenProgress(data)
      return data
    } catch {
      return null
    }
  }, [skillName])

  // Poll for progress while generation is running
  useEffect(() => {
    if (!skillName || !open) return
    const isRunning = genProgress?.status === 'running' || genProgress?.status === 'queued'
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    if (isRunning) {
      pollRef.current = setInterval(async () => {
        const p = await fetchGenProgress()
        if (p && (p.status === 'completed' || p.status === 'failed')) {
          clearInterval(pollRef.current)
          pollRef.current = null
          await fetchTopics()
        }
      }, 1500)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [genProgress?.status, skillName, open, fetchGenProgress, fetchTopics])

  useEffect(() => {
    if (!open) {
      setTopics([])
      setChecked({})
      setVersion(0)
      setUpdatedAt(null)
      setGenProgress(null)
    } else {
      fetchTopics()
      fetchGenProgress()
    }
  }, [fetchTopics, fetchGenProgress, open])

  const handleToggle = async (topicId, completed, childIds = []) => {
    // Optimistically update all
    setChecked(prev => {
      const next = { ...prev, [topicId]: completed }
      for (const cid of childIds) next[cid] = completed
      return next
    })
    try {
      // Save parent
      await fetch(`${API}/skill-roadmap-progress/${topicId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed })
      })
      // Save all children
      for (const cid of childIds) {
        await fetch(`${API}/skill-roadmap-progress/${cid}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed })
        })
      }
      if (onRefreshProgress) onRefreshProgress()
    } catch {
      // Revert on error
      setChecked(prev => {
        const next = { ...prev, [topicId]: completed ? 0 : 1 }
        for (const cid of childIds) next[cid] = completed ? 0 : 1
        return next
      })
    }
  }

  const handleGenerate = async () => {
    try {
      const res = await fetch(`${API}/skill-roadmaps/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName })
      })
      // 409 = already running, just poll for progress
      const data = await res.json().catch(() => ({}))
      if (res.status === 409) {
        fetchGenProgress()
      } else if (res.ok) {
        setGenProgress({ status: 'queued', step: 0, total_steps: 4, message: data.message || 'Queued' })
      }
    } catch {}
  }

  const handleExtend = async () => {
    try {
      const res = await fetch(`${API}/skill-roadmaps/extend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName })
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 409) {
        fetchGenProgress()
      } else if (res.ok) {
        setGenProgress({ status: 'queued', step: 0, total_steps: 4, message: data.message || 'Queued' })
      }
    } catch {}
  }

  const handleFinegrain = async () => {
    try {
      const res = await fetch(`${API}/skill-roadmaps/finegrain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName })
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 409) {
        fetchGenProgress()
      } else if (res.ok) {
        setGenProgress({ status: 'queued', step: 0, total_steps: 4, message: data.message || 'Queued' })
      }
    } catch {}
  }

  const total = countLeafTopics(topics)
  const done = countCheckedLeaves(topics, checked)
  const pct = total > 0 ? Math.round((done / total) * 100) : 0
  const isEmpty = topics.length === 0 && !loading
  const isRunning = genProgress?.status === 'running' || genProgress?.status === 'queued'
  const isFailed = genProgress?.status === 'failed'
  const genPct = genProgress ? Math.round(((genProgress.step || 0) / (genProgress.total_steps || 4)) * 100) : 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[420px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="p-6 pb-3">
          <SheetTitle className="flex items-center gap-2 text-base">
            {skillName}
            {!isEmpty && version > 0 && (
              <Badge variant="secondary" className="text-[0.5rem]">v{version}</Badge>
            )}
          </SheetTitle>
          <SheetDescription>
            {isEmpty && !isRunning
              ? 'No roadmap yet — generate one to start tracking'
              : isRunning
                ? genProgress?.message || 'Processing...'
                : (
                  <span className="flex items-center gap-2">
                    <span>{done}/{total} items completed</span>
                    {updatedAt && <span className="text-[0.55rem] opacity-60">Updated {formatTimestamp(updatedAt)}</span>}
                  </span>
                )
            }
          </SheetDescription>
        </SheetHeader>

        {/* Progress bar — roadmap generation */}
        {isRunning && (
          <div className="px-6 pb-3 space-y-2">
            <div className="flex items-center gap-2">
              <Progress value={genPct} className="h-1.5 flex-1" />
              <span className="text-[0.6rem] text-muted-foreground font-semibold shrink-0">{genProgress.step}/{genProgress.total_steps}</span>
            </div>
            <div className="flex gap-1">
              {['Preparing', 'Prompt', 'AI', 'Saving'].map((label, i) => (
                <div key={label} className={cn(
                  "flex-1 text-center text-[0.5rem] rounded py-0.5",
                  i < (genProgress.step || 0) ? "bg-green-500/15 text-green-500" :
                  i === (genProgress.step || 0) ? "bg-primary/15 text-primary font-semibold" :
                  "text-muted-foreground"
                )}>
                  {i < (genProgress.step || 0) ? '✓ ' : ''}{label}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="destructive"
                onClick={async () => {
                  try {
                    await fetch(`${API}/skill-roadmaps/cancel?skill=${encodeURIComponent(skillName)}`, { method: 'POST' })
                    setGenProgress({ status: 'cancelled', step: 0, total_steps: 4, message: 'Cancelled' })
                  } catch {}
                }}
                className="h-6 text-[0.6rem] gap-1"
              >
                <X className="w-3 h-3" /> Cancel
              </Button>
              <span className="text-[0.55rem] text-muted-foreground">Generation may take a moment</span>
            </div>
          </div>
        )}

        {/* Failed state */}
        {(isFailed || genProgress?.status === 'cancelled') && (
          <div className="px-6 pb-3">
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-red-500">
                  {genProgress?.status === 'cancelled' ? 'Generation Cancelled' : 'Generation Failed'}
                </span>
                <div className="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setGenProgress(null)
                      fetchGenProgress()
                    }}
                    className="h-6 text-[0.6rem] gap-1"
                  >
                    <ArrowsClockwise className="w-3 h-3" /> Refresh
                  </Button>
                  <Button
                    size="sm"
                    variant="default"
                    onClick={handleGenerate}
                    className="h-6 text-[0.6rem] gap-1"
                  >
                    <TreeStructure className="w-3 h-3" /> Regenerate
                  </Button>
                </div>
              </div>
              {/* Error message — scrollable, copyable, with tooltip */}
              <div
                className="relative group cursor-pointer"
                onClick={() => {
                  navigator.clipboard.writeText(genProgress.error || 'Generation failed')
                  toast.success('Error copied to clipboard')
                }}
                title={genProgress.error || 'Generation failed'}
              >
                <div className="text-[0.65rem] text-red-400 bg-red-500/10 rounded p-2 max-h-[80px] overflow-y-auto font-mono leading-relaxed">
                  {genProgress.error || 'Generation failed'}
                </div>
                <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Badge variant="secondary" className="text-[0.45rem] h-4 bg-background/80">Click to copy</Badge>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Progress bar — roadmap completion */}
        {!isEmpty && !isRunning && (
          <div className="px-6 pb-3">
            <div className="flex items-center gap-2">
              <Progress value={pct} className="h-1.5 flex-1" />
              <span className="text-[0.6rem] text-muted-foreground font-semibold shrink-0">{pct}%</span>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="px-6 pb-3">
          {isEmpty && !isRunning ? (
            <Button size="sm" onClick={handleGenerate} className="gap-1.5 h-8 text-xs font-semibold">
              <TreeStructure className="w-3.5 h-3.5" /> Generate Roadmap
            </Button>
          ) : isRunning ? (
            <div className="flex items-center gap-2">
              <Spinner className="w-4 h-4 animate-spin text-primary" />
              <span className="text-xs text-muted-foreground">{genProgress?.message || 'Working...'}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 flex-wrap">
              <Button size="sm" onClick={handleExtend} className="gap-1.5 h-8 text-xs font-semibold">
                <Lightning className="w-3.5 h-3.5" /> Extend
              </Button>
              <Button size="sm" variant="secondary" onClick={handleFinegrain} className="gap-1.5 h-8 text-xs font-semibold">
                <ArrowsClockwise className="w-3.5 h-3.5" /> Fine-grain
              </Button>
              <Button size="sm" variant="ghost" onClick={handleGenerate} className="gap-1.5 h-8 text-[0.65rem]">
                <ArrowsClockwise className="w-3 h-3" /> Regenerate
              </Button>
            </div>
          )}
        </div>

        {/* Roadmap tree */}
        <div className="flex-1 overflow-y-auto px-4 pb-6">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
              <Spinner className="w-4 h-4 animate-spin mr-2" /> Loading...
            </div>
          ) : isEmpty && !isRunning ? (
            <div className="text-center py-12 text-muted-foreground">
              <TreeStructure className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-semibold mb-1">No roadmap for this skill</p>
              <p className="text-[0.65rem] max-w-[240px] mx-auto">
                Generate a learning roadmap to track your progress from basic to advanced.
              </p>
            </div>
          ) : isRunning ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Spinner className="w-8 h-8 animate-spin mb-3 text-primary" />
              <p className="text-sm font-semibold">{genProgress?.message || 'Working...'}</p>
              <p className="text-[0.65rem] mt-1">This may take a moment</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {topics.map(topic => (
                <TopicNode key={topic.id} topic={topic} checked={checked} onToggle={handleToggle} />
              ))}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
