import { useState, useEffect, useCallback } from 'react'
import {
  TrendUp, Brain, BookOpen, ChartLineUp, Wrench, ArrowsClockwise, Target, TreeStructure, Plus, User, Spinner
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import SkillRoadmapDrawer from './SkillRoadmapDrawer'

const API = '/api'

function SkillRow({ skill, type, onClick, topicProgress }) {
  const levelColors = {
    expert: 'bg-green-500/15 text-green-500',
    advanced: 'bg-blue-500/15 text-blue-500',
    intermediate: 'bg-yellow-500/15 text-yellow-500',
    beginner: 'bg-orange-500/15 text-orange-500',
    none: 'bg-red-500/15 text-red-500',
  }
  const prog = topicProgress?.[skill.skill]
  const hasProgress = prog && prog.total > 0
  return (
    <div
      className="flex items-center gap-2 p-2 rounded hover:bg-muted transition text-xs cursor-pointer"
      onClick={() => onClick?.(skill.skill)}
    >
      <span className="font-semibold w-24 truncate">{skill.skill}</span>
      {/* Demand bar */}
      <div className="flex-1 space-y-1">
        <div className="h-[3px] rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary" style={{ width: `${skill.demandPercentage || 0}%` }} />
        </div>
        {/* Topic progress bar */}
        {hasProgress && (
          <div className="h-[3px] rounded-full bg-muted">
            <div
              className={cn("h-full rounded-full transition-all",
                prog.pct === 100 ? "bg-green-500" : prog.pct > 0 ? "bg-emerald-400" : "bg-muted"
              )}
              style={{ width: `${prog.pct}%` }}
            />
          </div>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="w-8 text-right text-[0.55rem] text-muted-foreground">{skill.demandPercentage || 0}%</span>
        {hasProgress ? (
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3",
            prog.pct === 100 ? "bg-green-500/15 text-green-500" :
            prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" :
            "bg-gray-500/15 text-gray-400"
          )}>
            {prog.pct}%
          </Badge>
        ) : (
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0", levelColors[skill.candidateLevel || skill.currentLevel] || 'bg-gray-500/15 text-gray-400')}>
            {skill.candidateLevel || skill.currentLevel}
          </Badge>
        )}
      </div>
    </div>
  )
}

function RecommendationCard({ rec, onClick, topicProgress }) {
  const prog = topicProgress?.[rec.skill]
  const hasProgress = prog && prog.total > 0
  return (
    <div
      className="p-2 rounded-lg border border-primary/20 bg-primary/5 space-y-1 cursor-pointer hover:border-primary/40 transition"
      onClick={() => onClick?.(rec.skill)}
    >
      <div className="flex items-center justify-between">
        <span className="font-bold text-xs">{rec.skill}</span>
        <div className="flex items-center gap-1">
          {hasProgress && (
            <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
              prog.pct === 100 ? "bg-green-500/15 text-green-500" :
              prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" :
              "bg-gray-500/15 text-gray-400"
            )}>
              {prog.done}/{prog.total}
            </Badge>
          )}
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
            rec.roi >= 8 ? "bg-green-500/15 text-green-500" :
            rec.roi >= 6 ? "bg-yellow-500/15 text-yellow-500" : "bg-gray-500/15 text-gray-400"
          )}>ROI: {rec.roi}/10</Badge>
        </div>
      </div>
      <div className="text-[0.55rem] text-muted-foreground">{rec.reason}</div>
      <div className="flex items-center gap-2 text-[0.5rem] text-muted-foreground">
        <span>Demand: {rec.demandPercentage}%</span>
        <span>·</span>
        <span>Effort: {rec.learningEffort}</span>
      </div>
      {hasProgress && prog.pct > 0 && (
        <Progress value={prog.pct} className="h-1 mt-1" />
      )}
    </div>
  )
}

export default function SkillsIntelSection({ data, refreshing, onRefresh, topicProgress, onRefreshProgress, genJobs = [] }) {
  const skills = data?.skills || {}
  const strengths = skills.strengths || []
  const gaps = skills.gaps || []
  const recommendations = skills.learningRecommendations || []
  const [selectedSkill, setSelectedSkill] = useState(null)
  const [customSkillInput, setCustomSkillInput] = useState('')
  const [techStackSkills, setTechStackSkills] = useState([])

  // Fetch tech_stack to show ALL skills (even without topics)
  useEffect(() => {
    fetch(`${API}/tech-stack`)
      .then(r => r.json())
      .then(list => setTechStackSkills(Array.isArray(list) ? list : []))
      .catch(() => {})
  }, [topicProgress])

  // All skills from AI results
  const aiSkills = [...new Set([...strengths, ...gaps, ...recommendations.map(r => r.skill)].map(s => s.skill || s))]

  // All skills = tech_stack (includes both AI and user-added)
  const allSkillNames = [...new Set([...techStackSkills.map(s => s.name), ...aiSkills])]

  const handleAddCustomSkill = async () => {
    const name = customSkillInput.trim()
    if (!name) return
    // Add to tech_stack so it persists
    try {
      await fetch(`${API}/tech-stack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, level: 1 })
      })
      setCustomSkillInput('')
      // Refresh progress to include new skill
      if (onRefreshProgress) onRefreshProgress()
      // Open the drawer for this skill to generate topics
      setSelectedSkill(name)
    } catch {}
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Skills Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.skills} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.skills && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { n: strengths.length, l: 'Strengths', c: 'text-green-500', icon: <TrendUp className="w-5 h-5" /> },
          { n: gaps.length, l: 'Skill Gaps', c: 'text-red-500', icon: <BookOpen className="w-5 h-5" /> },
          { n: recommendations.length, l: 'Recommendations', c: 'text-blue-500', icon: <Brain className="w-5 h-5" /> },
          { n: recommendations.filter(r => r.roi >= 8).length, l: 'High ROI', c: 'text-yellow-500', icon: <ChartLineUp className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      {/* Skill Roadmaps section */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <TreeStructure className="w-5 h-5 text-emerald-500" />
          <h4 className="font-extrabold text-sm">Skill Roadmaps</h4>
          <Badge variant="secondary" className="text-[0.5rem] bg-emerald-500/15 text-emerald-500">{allSkillNames.filter(s => topicProgress[s]?.total > 0).length}</Badge>
        </div>

        {/* Generation progress banners — only under this section */}
        {genJobs.length > 0 && genJobs.map(job => (
          <div
            key={job.skill}
            className="mb-2 p-2 rounded-lg border border-primary/30 bg-primary/5 flex items-center gap-2 cursor-pointer hover:border-primary/50 transition"
            onClick={() => setSelectedSkill(job.skill)}
          >
            <Spinner className="w-3.5 h-3.5 text-primary animate-spin shrink-0" />
            <span className="text-xs font-semibold">{job.skill}</span>
            <span className="text-[0.6rem] text-muted-foreground">{job.message || 'Working...'}</span>
            <div className="flex-1">
              <Progress value={job.total_steps ? ((job.step || 0) / job.total_steps) * 100 : 0} className="h-1" />
            </div>
            <span className="text-[0.55rem] text-muted-foreground shrink-0">{job.step || 0}/{job.total_steps || 4}</span>
            {job.session_id && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigator.clipboard.writeText(job.session_id)
                  toast.success('Session ID copied')
                }}
                className="text-[0.5rem] text-muted-foreground hover:text-foreground font-mono truncate max-w-[80px] shrink-0"
                title={`Click to copy: ${job.session_id}`}
              >
                {job.session_id.slice(0, 8)}...
              </button>
            )}
          </div>
        ))}

        <div className="space-y-2">
          {allSkillNames.map(skill => {
            const prog = topicProgress[skill]
            const hasRoadmap = prog && prog.total > 0
            const isUser = techStackSkills.some(s => s.name === skill && s.source === 'user')
            if (!hasRoadmap) return null
            return (
              <div
                key={skill}
                className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition cursor-pointer"
                onClick={() => setSelectedSkill(skill)}
              >
                <span className="text-xs font-semibold w-24 truncate">{skill}</span>
                {isUser && (
                  <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-purple-500/15 text-purple-500 shrink-0 gap-0.5">
                    <User className="w-2.5 h-2.5" /> Custom
                  </Badge>
                )}
                <div className="flex-1">
                  <Progress value={prog.pct} className="h-1.5" />
                </div>
                <span className="text-[0.6rem] text-muted-foreground w-12 text-right shrink-0">
                  {prog.completed}/{prog.total}
                </span>
                <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0",
                  prog.pct === 100 ? "bg-green-500/15 text-green-500" :
                  prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" :
                  "bg-gray-500/15 text-gray-400"
                )}>{prog.pct}%</Badge>
              </div>
            )
          })}
          {/* Add custom skill */}
          <div className="flex items-center gap-2 pt-2 border-t">
            <Input
              value={customSkillInput}
              onChange={(e) => setCustomSkillInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCustomSkill()}
              placeholder="Add custom skill..."
              className="h-7 text-xs flex-1"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={handleAddCustomSkill}
              disabled={!customSkillInput.trim()}
              className="h-7 gap-1 text-[0.6rem]"
            >
              <Plus className="w-3 h-3" /> Add
            </Button>
          </div>
        </div>
      </Card>

      {/* Custom Skills — user-added, no roadmap yet */}
      {allSkillNames.filter(s => {
        const prog = topicProgress[s]
        return !prog || prog.total === 0
      }).length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <User className="w-5 h-5 text-purple-500" />
            <h4 className="font-extrabold text-sm">Custom Skills</h4>
            <Badge variant="secondary" className="text-[0.5rem] bg-purple-500/15 text-purple-500">
              {allSkillNames.filter(s => {
                const prog = topicProgress[s]
                return !prog || prog.total === 0
              }).length}
            </Badge>
          </div>
          <div className="space-y-2">
            {allSkillNames.filter(s => {
              const prog = topicProgress[s]
              return !prog || prog.total === 0
            }).map(skill => {
              const isUser = techStackSkills.some(s => s.name === skill && s.source === 'user')
              return (
                <div
                  key={skill}
                  className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition cursor-pointer"
                  onClick={() => setSelectedSkill(skill)}
                >
                  <span className="text-xs font-semibold w-24 truncate">{skill}</span>
                  {isUser && (
                    <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-purple-500/15 text-purple-500 shrink-0 gap-0.5">
                      <User className="w-2.5 h-2.5" /> Custom
                    </Badge>
                  )}
                  <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap yet</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedSkill(skill)
                    }}
                    className="h-5 text-[0.5rem] gap-0.5"
                  >
                    <TreeStructure className="w-2.5 h-2.5" /> Generate
                  </Button>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Strengths */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendUp className="w-5 h-5 text-green-500" />
              <h4 className="font-extrabold text-sm">Strengths</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-green-500/15 text-green-500">{strengths.length}</Badge>
            </div>
            <div className="space-y-1">
              {strengths.length > 0 ? strengths.map((s, i) => (
                <SkillRow key={i} skill={s} type="strength" onClick={setSelectedSkill} topicProgress={topicProgress} />
              )) : (
                <div className="text-xs text-muted-foreground">No strengths identified yet</div>
              )}
            </div>
          </Card>

          {/* Gaps */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5 text-red-500" />
              <h4 className="font-extrabold text-sm">Skill Gaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-red-500/15 text-red-500">{gaps.length}</Badge>
            </div>
            <div className="space-y-1">
              {gaps.length > 0 ? gaps.map((g, i) => (
                <SkillRow key={i} skill={g} type="gap" onClick={setSelectedSkill} topicProgress={topicProgress} />
              )) : (
                <div className="text-xs text-muted-foreground">No major gaps identified</div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          {/* Learning Recommendations */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-primary" />
              <h4 className="font-extrabold text-sm">Learning Recommendations</h4>
            </div>
            <div className="space-y-2">
              {recommendations.length > 0 ? recommendations.map((r, i) => (
                <RecommendationCard key={i} rec={r} onClick={setSelectedSkill} topicProgress={topicProgress} />
              )) : (
                <div className="text-xs text-muted-foreground text-center py-4">No recommendations yet</div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Skill Topic Drawer */}
      <SkillRoadmapDrawer
        skillName={selectedSkill}
        open={!!selectedSkill}
        onOpenChange={(open) => { if (!open) setSelectedSkill(null) }}
        onRefreshProgress={onRefreshProgress}
      />
    </div>
  )
}
