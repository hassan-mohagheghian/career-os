'use client'

import { useState, useEffect, useCallback } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/shared/ui/tabs'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import { useLocalHistory } from '@/shared/hooks'
import {
  Star, Lightning, Plus, ArrowsClockwise, CaretDown, CaretRight, Check, Spinner,
  PencilSimple, Trash, Code,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import type { SkillListItem } from '@/entities/skill/types'
import { CategoryBadge, OriginBadge } from './SkillRow'

function RoadmapNode({ node, depth = 0 }: { node: any; depth?: number }) {
  const [open, setOpen] = useState(depth < 2)
  const hasChildren = node.children?.length > 0
  const isDone = node.completed || node.progress === 'completed'

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1.5 py-1 px-1 rounded hover:bg-muted/50 cursor-pointer text-xs",
          isDone && "text-muted-foreground"
        )}
        style={{ paddingLeft: `${8 + depth * 16}px` }}
      >
        {hasChildren ? (
          <button onClick={() => setOpen(!open)} className="p-0.5 hover:bg-muted rounded">
            {open ? <CaretDown className="w-3 h-3" /> : <CaretRight className="w-3 h-3" />}
          </button>
        ) : (
          <span className="w-4" />
        )}
        <span className="w-3 h-3 rounded border flex items-center justify-center shrink-0">
          {isDone && <Check className="w-2 h-2 text-green-500" />}
        </span>
        <span className={cn(isDone && "line-through")}>{node.name || node.title}</span>
        {node.status === 'running' && <Spinner className="w-3 h-3 animate-spin text-primary" />}
      </div>
      {open && hasChildren && (
        <div>
          {node.children.map((child: any, i: number) => (
            <RoadmapNode key={child.id || i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

interface SkillDetailDrawerProps {
  skillId: number | null
  skill: SkillListItem | null
  onOpenChange: (id: number | null) => void
  onEdit: (id: number) => void
  onDelete: (id: number) => void
  onRefresh: () => void
}

export function SkillDetailDrawer({
  skillId,
  skill,
  onOpenChange,
  onEdit,
  onDelete,
  onRefresh,
}: SkillDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState('details')
  const [roadmapTree, setRoadmapTree] = useState<any[]>([])
  const [loadingRoadmap, setLoadingRoadmap] = useState(false)
  const [generating, setGenerating] = useState(false)

  const { items: skillHistory, singleRunning, refresh: refreshHistory } = useLocalHistory({
    context: 'skill',
    skill_name: skill?.name,
    enabled: !!skill?.name,
  })

  const skillName = skill?.name || ''
  const open = !!skill && !!skillId

  const fetchRoadmap = useCallback(async (name: string) => {
    setLoadingRoadmap(true)
    try {
      const res = await fetch(`/api/skill-roadmaps?skill=${encodeURIComponent(name)}`)
      if (res.ok) {
        const data = await res.json()
        setRoadmapTree(data.roadmap || [])
      } else {
        setRoadmapTree([])
      }
    } catch {
      setRoadmapTree([])
    } finally {
      setLoadingRoadmap(false)
    }
  }, [])

  useEffect(() => {
    if (open && skillName) {
      fetchRoadmap(skillName)
    }
  }, [open, skillName, fetchRoadmap])

  const runRoadmapAction = useCallback(async (endpoint: string, skillName: string) => {
    if (generating) return
    setGenerating(true)
    try {
      const res = await fetch(`/api/skill-roadmaps/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName }),
      })
      if (res.ok) {
        onRefresh()
        await fetchRoadmap(skillName)
      }
    } finally {
      setGenerating(false)
    }
  }, [generating, onRefresh, fetchRoadmap])

  if (!skill) return null

  const confidence = skill.confidence != null ? Math.round(skill.confidence * 100) : null
  const demand = skill.market_relevance != null ? Math.round(skill.market_relevance * 100) : null

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onOpenChange(null) }}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5 text-primary shrink-0" />
            <span className="truncate">{skill.name}</span>
            <CategoryBadge category={skill.category} />
            <OriginBadge sourceType={skill.source_type} />
          </SheetTitle>
          {onEdit && skillId != null && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 text-xs text-muted-foreground"
              onClick={() => onEdit(skillId as number)}
              aria-label="Edit skill"
            >
              <PencilSimple className="w-3.5 h-3.5" /> Edit
            </Button>
          )}
        </SheetHeader>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
          <TabsList className="px-4 pt-2 shrink-0">
            <TabsTrigger value="details" className="text-2xs">Details</TabsTrigger>
            <TabsTrigger value="roadmap" className="text-2xs">Roadmap</TabsTrigger>
            <TabsTrigger value="history" className="text-2xs">History</TabsTrigger>
          </TabsList>
          <ScrollArea className="flex-1 min-h-0">
            <div className="px-4 py-3 space-y-4">
              {activeTab === 'details' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    {skill.level > 0 && (
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-yellow-500" />
                        <span className="text-xs font-bold">Lv.{skill.level}</span>
                      </div>
                    )}
                    {confidence != null && (
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-muted-foreground">Confidence:</span>
                        <span className={cn("text-xs font-bold",
                          confidence >= 80 ? "text-green-500" : confidence >= 50 ? "text-yellow-500" : "text-orange-500"
                        )}>
                          {confidence}%
                        </span>
                      </div>
                    )}
                    {demand != null && (
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-muted-foreground">Market:</span>
                        <span className={cn("text-xs font-bold",
                          demand >= 80 ? "text-green-500" : demand >= 50 ? "text-yellow-500" : "text-orange-500"
                        )}>
                          {demand}%
                        </span>
                      </div>
                    )}
                  </div>

                  {skill.roles && (
                    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Relevant Roles</p>
                      <p className="text-xs text-foreground">{skill.roles}</p>
                    </div>
                  )}

                  {skill.path && (
                    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Path</p>
                      <p className="text-xs text-foreground whitespace-pre-wrap">{skill.path}</p>
                    </div>
                  )}

                  {skill.tags && skill.tags.length > 0 && (
                    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Tags</p>
                      <div className="flex flex-wrap gap-1">
                        {skill.tags.map((t, i) => (
                          <Badge key={i} variant="secondary" className="text-2xs">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {skill.aliases && skill.aliases.length > 0 && (
                    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Also Known As</p>
                      <div className="flex flex-wrap gap-1">
                        {skill.aliases.map((a, i) => (
                          <Badge key={i} variant="outline" className="text-2xs">{a}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {skill.evidence && skill.evidence !== '[]' && (
                    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Why This Skill Matters</p>
                      <p className="text-xs text-muted-foreground">{skill.evidence}</p>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline" size="sm"
                      onClick={() => runRoadmapAction('generate', skillName)}
                      disabled={generating}
                      className="h-6 text-2xs gap-1"
                    >
                      {generating ? <Spinner className="w-3 h-3 animate-spin" /> : <Lightning className="w-3 h-3" />}
                      Generate Roadmap
                    </Button>
                  </div>
                </div>
              )}

              {activeTab === 'roadmap' && (
                <div className="space-y-4">
                  {singleRunning && (
                    <GenerationProgressCard
                      type="roadmap"
                      progress={{
                        running: singleRunning.status === 'processing' || singleRunning.status === 'running' || singleRunning.status === 'queued',
                        status: singleRunning.status,
                        message: singleRunning.title,
                        session_id: singleRunning.session_id,
                      }}
                      title="Generating roadmap..."
                      compact
                      className={undefined}
                      elapsed={undefined}
                      onCancel={() => {}}
                      onRetry={() => {}}
                    />
                  )}

                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => runRoadmapAction('generate', skillName)} disabled={generating} className="h-6 text-2xs gap-1">
                      {generating ? <Spinner className="w-3 h-3 animate-spin" /> : <Lightning className="w-3 h-3" />}
                      Generate
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => runRoadmapAction('extend', skillName)} disabled={generating || !roadmapTree?.length} className="h-6 text-2xs gap-1">
                      <Plus className="w-3 h-3" /> Extend
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => runRoadmapAction('finegrain', skillName)} disabled={generating || !roadmapTree?.length} className="h-6 text-2xs gap-1">
                      <ArrowsClockwise className="w-3 h-3" /> Finegrain
                    </Button>
                  </div>

                  {loadingRoadmap ? (
                    <div className="flex items-center justify-center py-6">
                      <Spinner className="w-4 h-4 animate-spin text-primary" />
                    </div>
                  ) : roadmapTree && roadmapTree.length > 0 ? (
                    <div className="space-y-1">
                      {roadmapTree.map((node, i) => (
                        <RoadmapNode key={node.id || i} node={node} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-2xs text-muted-foreground">
                      No roadmap yet. Generate one to see learning path recommendations.
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-2">
                  {skillHistory.length === 0 && (
                    <div className="text-center py-6 text-2xs text-muted-foreground">
                      No generation history for this skill.
                    </div>
                  )}
                  {skillHistory.map((item: any) => (
                    <GenerationHistoryItem key={item.id || item.run_id} item={item} />
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>
        </Tabs>
        <div className="flex items-center justify-end gap-2 border-t border-border/40 px-4 py-3 shrink-0">
          <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs text-destructive" onClick={() => skillId != null && onDelete(skillId)}>
            <Trash className="w-3 h-3" /> Delete
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
