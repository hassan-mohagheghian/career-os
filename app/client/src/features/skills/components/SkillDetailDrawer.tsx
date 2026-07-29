import { useState, useEffect, useCallback } from 'react'
import {
  X, Code, Star, ArrowsClockwise, CaretDown, CaretRight, Check,
  Lightning, Plus, Spinner, Note,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/shared/ui/tabs'
import { AppDrawer, Section } from '@/shared/components/DrawerComponents'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import { useLocalHistory } from '@/shared/hooks'

const CATEGORY_COLORS: Record<string, string> = {
  'language': 'text-blue-500 bg-blue-500/10',
  'framework': 'text-green-500 bg-green-500/10',
  'tool': 'text-orange-500 bg-orange-500/10',
  'concept': 'text-purple-500 bg-purple-500/10',
  'platform': 'text-cyan-500 bg-cyan-500/10',
}

function SkillBadge({ category }: { category?: string }) {
  if (!category) return null
  const colors = CATEGORY_COLORS[category.toLowerCase()] || 'text-muted-foreground bg-muted'
  return (
    <span className={cn("text-2xs px-1 py-0 rounded", colors)}>
      {category}
    </span>
  )
}

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

const STEP_CONFIG = {
  steps: [
    { id: 'extract', label: 'Extract', icon: '🔍' },
    { id: 'generate', label: 'Generating', icon: '⚡' },
    { id: 'save', label: 'Saving', icon: '💾' },
    { id: 'done', label: 'Done', icon: '✅' },
  ],
}

export default function SkillDetailDrawer({
  skill,
  roadmapTree,
  roadmapProgress,
  onClose,
  onRefreshSkills,
  onGenerateRoadmap,
  onExtendRoadmap,
  onFinegrainRoadmap,
}: {
  skill: any
  roadmapTree?: any[]
  roadmapProgress?: Record<string, any>
  onClose: () => void
  onRefreshSkills?: () => void
  onGenerateRoadmap?: (skillName: string) => void
  onExtendRoadmap?: (skillName: string) => void
  onFinegrainRoadmap?: (skillName: string) => void
}) {
  const [activeTab, setActiveTab] = useState('details')
  const [generating, setGenerating] = useState(false)

  const { items: skillHistory, singleRunning, refresh: refreshHistory } = useLocalHistory({
    context: 'skill',
    skill_name: skill?.name,
    enabled: !!skill?.name,
  })

  const skillName = skill?.name || ''
  const genJob = skillName ? null : null

  const handleGenerate = useCallback(async () => {
    if (!skillName || generating) return
    setGenerating(true)
    try {
      const res = await fetch(`/api/skill-roadmaps/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName }),
      })
      if (res.ok) {
        onGenerateRoadmap?.(skillName)
      }
    } finally {
      setGenerating(false)
    }
  }, [skillName, generating, onGenerateRoadmap])

  const handleExtend = useCallback(async () => {
    if (!skillName || generating) return
    setGenerating(true)
    try {
      const res = await fetch(`/api/skill-roadmaps/extend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName }),
      })
      if (res.ok) {
        onExtendRoadmap?.(skillName)
      }
    } finally {
      setGenerating(false)
    }
  }, [skillName, generating, onExtendRoadmap])

  const handleFinegrain = useCallback(async () => {
    if (!skillName || generating) return
    setGenerating(true)
    try {
      const res = await fetch(`/api/skill-roadmaps/finegrain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName }),
      })
      if (res.ok) {
        onFinegrainRoadmap?.(skillName)
      }
    } finally {
      setGenerating(false)
    }
  }, [skillName, generating, onFinegrainRoadmap])

  if (!skill) return null

  return (
    <AppDrawer open={!!skill} onOpenChange={(open) => { if (!open) onClose() }}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Code className="w-4 h-4 text-primary shrink-0" />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-semibold truncate">{skill.name}</span>
                {skill.category && <SkillBadge category={skill.category} />}
              </div>
              {skill.roles && (
                <div className="text-2xs text-muted-foreground truncate">{skill.roles}</div>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-muted rounded shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
          <TabsList className="px-4 pt-2 shrink-0">
            <TabsTrigger value="details" className="text-2xs">Details</TabsTrigger>
            <TabsTrigger value="roadmap" className="text-2xs">Roadmap</TabsTrigger>
            <TabsTrigger value="history" className="text-2xs">History</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
            {/* Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-4">
                {/* Stats */}
                <div className="flex items-center gap-4">
                  {skill.level > 0 && (
                    <div className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-yellow-500" />
                      <span className="text-xs font-bold">Lv.{skill.level}</span>
                    </div>
                  )}
                  {skill.confidence != null && (
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-muted-foreground">Confidence:</span>
                      <span className={cn("text-xs font-bold",
                        skill.confidence >= 0.8 ? "text-green-500" : skill.confidence >= 0.5 ? "text-yellow-500" : "text-orange-500"
                      )}>
                        {Math.round(skill.confidence * 100)}%
                      </span>
                    </div>
                  )}
                  {skill.market_relevance != null && (
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-muted-foreground">Market:</span>
                      <span className={cn("text-xs font-bold",
                        skill.market_relevance >= 0.8 ? "text-green-500" : skill.market_relevance >= 0.5 ? "text-yellow-500" : "text-orange-500"
                      )}>
                        {Math.round(skill.market_relevance * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Tags */}
                {skill.tags?.length > 0 && (
                  <Section title="Tags" icon={<Code className="w-3 h-3" />}>
                    <div className="flex flex-wrap gap-1">
                      {skill.tags.map((t: string, i: number) => (
                        <Badge key={i} variant="secondary" className="text-2xs">{t}</Badge>
                      ))}
                    </div>
                  </Section>
                )}

                {/* Aliases */}
                {skill.aliases?.length > 0 && (
                  <Section title="Also Known As" icon={<Code className="w-3 h-3" />}>
                    <div className="flex flex-wrap gap-1">
                      {skill.aliases.map((a: string, i: number) => (
                        <Badge key={i} variant="outline" className="text-2xs">{a}</Badge>
                      ))}
                    </div>
                  </Section>
                )}

                {/* Evidence */}
                {skill.evidence && (
                  <Section title="Why This Skill Matters" icon={<Note className="w-3 h-3" />}>
                    <p className="text-xs text-muted-foreground">{skill.evidence}</p>
                  </Section>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2">
                  <Button
                    variant="outline" size="sm"
                    onClick={handleGenerate}
                    disabled={generating}
                    className="h-6 text-2xs gap-1"
                  >
                    {generating ? <Spinner className="w-3 h-3 animate-spin" /> : <Lightning className="w-3 h-3" />}
                    Generate Roadmap
                  </Button>
                </div>
              </div>
            )}

            {/* Roadmap Tab */}
            {activeTab === 'roadmap' && (
              <div className="space-y-4">
                {singleRunning && (
                  <GenerationProgressCard
                    running={singleRunning}
                    stepConfig={STEP_CONFIG}
                    compact
                  />
                )}

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline" size="sm"
                    onClick={handleGenerate}
                    disabled={generating}
                    className="h-6 text-2xs gap-1"
                  >
                    {generating ? <Spinner className="w-3 h-3 animate-spin" /> : <Lightning className="w-3 h-3" />}
                    Generate
                  </Button>
                  <Button
                    variant="outline" size="sm"
                    onClick={handleExtend}
                    disabled={generating || !roadmapTree?.length}
                    className="h-6 text-2xs gap-1"
                  >
                    <Plus className="w-3 h-3" /> Extend
                  </Button>
                  <Button
                    variant="outline" size="sm"
                    onClick={handleFinegrain}
                    disabled={generating || !roadmapTree?.length}
                    className="h-6 text-2xs gap-1"
                  >
                    <ArrowsClockwise className="w-3 h-3" /> Finegrain
                  </Button>
                </div>

                {roadmapTree && roadmapTree.length > 0 ? (
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

            {/* History Tab */}
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
        </Tabs>
      </div>
    </AppDrawer>
  )
}