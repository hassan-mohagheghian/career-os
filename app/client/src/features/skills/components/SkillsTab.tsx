import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Brain, ArrowsClockwise, Code, Spinner,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { useSkills } from '../hooks/useSkills'
import SkillDetailDrawer from './SkillDetailDrawer'

function MiniStat({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn("text-lg font-extrabold", color)}>{value}</span>
      <span className="text-2xs text-muted-foreground">{label}</span>
    </div>
  )
}

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

const ALL_CATEGORIES = '__all__'

export default function SkillsTab({ deepLinkSkill, onClearDeepLink }: { deepLinkSkill?: string | null; onClearDeepLink?: () => void } = {}) {
  const {
    skills, skillRoadmapProgress, skillGenJobs,
    fetchSkills, dashboardData,
    refresh, refreshing,
  } = useSkills()

  const [selectedSkill, setSelectedSkill] = useState<any | null>(null)
  const [roadmapTree, setRoadmapTree] = useState<any[]>([])
  const [loadingRoadmap, setLoadingRoadmap] = useState(false)
  const [activeCategory, setActiveCategory] = useState(ALL_CATEGORIES)

  const activeJobs = skillGenJobs.filter((j: any) => j.status === 'running' || j.status === 'queued')
  const summary = dashboardData?.summary || {}
  const isRunning = refreshing || activeJobs.length > 0

  // Compute categories from skills
  const categories = useMemo(() => {
    const cats = new Set<string>()
    skills.forEach((s: any) => { if (s.category) cats.add(s.category) })
    return Array.from(cats).sort()
  }, [skills])

  // Filter skills by active category
  const filteredSkills = useMemo(() => {
    if (activeCategory === ALL_CATEGORIES) return skills
    return skills.filter((s: any) => s.category === activeCategory)
  }, [skills, activeCategory])

  // Fetch roadmap tree when a skill is selected
  const fetchRoadmap = useCallback(async (skillName: string) => {
    setLoadingRoadmap(true)
    try {
      const res = await fetch(`/api/skill-roadmaps?skill=${encodeURIComponent(skillName)}`)
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

  // Open drawer for a skill
  const openSkill = useCallback((skill: any) => {
    setSelectedSkill(skill)
    fetchRoadmap(skill.name)
  }, [fetchRoadmap])

  const closeSkill = useCallback(() => {
    setSelectedSkill(null)
    setRoadmapTree([])
    onClearDeepLink?.()
  }, [onClearDeepLink])

  // Handle deep link
  useEffect(() => {
    if (deepLinkSkill) {
      const found = skills.find((s: any) => s.name === deepLinkSkill)
      if (found) {
        openSkill(found)
      }
    }
  }, [deepLinkSkill, skills, openSkill])

  // Refresh skills and roadmap after generation
  const handleGenerate = useCallback(async (skillName: string) => {
    fetchSkills()
    await fetchRoadmap(skillName)
  }, [fetchSkills, fetchRoadmap])

  return (
    <div className="space-y-5">
      {/* Intelligence Summary Header */}
      {summary.total_skills > 0 && (
        <Card className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-1.5">
                <Brain className="w-4 h-4 text-primary" />
                <span className="text-xs font-extrabold">Skills Overview</span>
              </div>
              <MiniStat label="skills" value={summary.total_skills} color="text-blue-500" />
              <MiniStat label="strengths" value={summary.strengths_count} color="text-green-500" />
              <MiniStat label="gaps" value={summary.gaps_count} color="text-orange-500" />
              <MiniStat label="roadmaps" value={summary.roadmap_skills} color="text-purple-500" />
              {summary.career_readiness_score > 0 && (
                <div className="flex items-center gap-1">
                  <span className={cn("text-lg font-extrabold",
                    summary.career_readiness_score >= 70 ? "text-green-500" :
                    summary.career_readiness_score >= 40 ? "text-yellow-500" : "text-red-500"
                  )}>{summary.career_readiness_score}</span>
                  <span className="text-2xs text-muted-foreground">readiness</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline" size="sm"
                onClick={() => refresh()}
                disabled={isRunning}
                className="gap-1 h-6 text-2xs"
              >
                <ArrowsClockwise className={cn("w-3 h-3", isRunning && "animate-spin")} />
                {isRunning ? 'Analyzing...' : 'Refresh'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Card className="p-2">
          <div className="flex items-center gap-2">
            <Spinner className="w-3 h-3 animate-spin text-primary" />
            <span className="text-2xs text-muted-foreground">
              Generating roadmap{activeJobs.length > 1 ? 's' : ''}: {activeJobs.map((j: any) => j.skill_name).join(', ')}
            </span>
          </div>
        </Card>
      )}

      {/* Skills List */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Code className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold">Skills</span>
          <Badge variant="secondary" className="text-2xs">{filteredSkills.length}</Badge>
        </div>

        {/* Category Filter Tabs */}
        {categories.length > 1 && (
          <div className="flex flex-wrap gap-1 mb-2">
            <button
              onClick={() => setActiveCategory(ALL_CATEGORIES)}
              className={cn("h-5 px-1.5 rounded text-2xs border transition-colors",
                activeCategory === ALL_CATEGORIES
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground border-border hover:bg-muted"
              )}
            >
              All
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={cn("h-5 px-1.5 rounded text-2xs border transition-colors",
                  activeCategory === cat
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background text-muted-foreground border-border hover:bg-muted"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {filteredSkills.length === 0 && (
          <div className="text-center py-6 text-2xs text-muted-foreground">
            No skills yet. Add one or run an AI analysis.
          </div>
        )}

        <div className="space-y-1">
          {filteredSkills.map((skill: any) => {
            const hasRoadmap = skillRoadmapProgress?.[skill.name]
            return (
              <div
                key={skill.id}
                onClick={() => openSkill(skill)}
                className="group flex items-start gap-2 rounded border bg-muted/50 px-2.5 py-1.5 text-xs cursor-pointer hover:bg-muted transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium truncate">{skill.name}</span>
                    {skill.category && <SkillBadge category={skill.category} />}
                    {skill.level > 0 && (
                      <span className="text-2xs text-muted-foreground shrink-0">Lv.{skill.level}</span>
                    )}
                  </div>
                  {skill.roles && (
                    <div className="text-2xs text-muted-foreground truncate mt-0.5">{skill.roles}</div>
                  )}
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {skill.tags.slice(0, 3).map((t: string, i: number) => (
                        <span key={i} className="text-2xs text-muted-foreground bg-muted px-1 py-0 rounded">{t}</span>
                      ))}
                      {skill.tags.length > 3 && (
                        <span className="text-2xs text-muted-foreground">+{skill.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                  {/* Roadmap progress bar */}
                  {hasRoadmap && (
                    <div className="flex items-center gap-1 mt-1">
                      <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden max-w-[120px]">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${Math.min(100, skillRoadmapProgress[skill.name].progress || 0)}%` }}
                        />
                      </div>
                      <span className="text-2xs text-muted-foreground">
                        {skillRoadmapProgress[skill.name].completed || 0}/{skillRoadmapProgress[skill.name].total || 0}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0 mt-0.5">
                  {skill.confidence != null && (
                    <span className="text-2xs text-muted-foreground" title={`Confidence: ${skill.confidence}`}>
                      {skill.confidence >= 0.8 ? '★' : skill.confidence >= 0.5 ? '☆' : '○'}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Skill Detail Drawer */}
      <SkillDetailDrawer
        skill={selectedSkill}
        roadmapTree={roadmapTree}
        roadmapProgress={skillRoadmapProgress?.[selectedSkill?.name]}
        onClose={closeSkill}
        onRefreshSkills={fetchSkills}
        onGenerateRoadmap={handleGenerate}
        onExtendRoadmap={handleGenerate}
        onFinegrainRoadmap={handleGenerate}
      />
    </div>
  )
}