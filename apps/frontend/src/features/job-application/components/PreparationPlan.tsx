'use client'

import { CircleNotch, Lightning } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import DateTime from '@/shared/components/DateTime'
import type { ApplicationPreparation, HardSkillRecommendation, SoftSkillRecommendation } from '@/entities/application/types'
import { useGeneratePreparationMutation } from '@/entities/application/hooks'

interface PreparationPlanProps {
  applicationId: string
  preparation: ApplicationPreparation | null
  generating: boolean
  onGenerate: () => void
}

const gapLabels: Record<string, string> = {
  missing: 'Missing',
  low: 'Low',
  matching: 'Matching',
}

const priorityColors: Record<string, string> = {
  high: 'text-red-500 bg-red-500/10 border-red-500/20',
  medium: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
  low: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
}

function PriorityTag({ priority }: { priority: string | null }) {
  if (!priority) return null
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-medium border ${priorityColors[priority] || ''}`}>
      {priority}
    </span>
  )
}

function HardSkillCard({ skill }: { skill: HardSkillRecommendation }) {
  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-foreground">{skill.skill}</p>
        <div className="flex items-center gap-1.5 shrink-0">
          {skill.gap_level && (
            <span className="text-2xs text-muted-foreground">{gapLabels[skill.gap_level] ?? skill.gap_level}</span>
          )}
          <PriorityTag priority={skill.priority} />
        </div>
      </div>
      {skill.why && <p className="text-xs text-muted-foreground whitespace-pre-wrap">{skill.why}</p>}
      <BulletList title="What to learn" items={skill.what_to_learn} />
      <BulletList title="How to practice" items={skill.how_to_practice} />
      <BulletList title="Resources" items={skill.resources} />
      {skill.estimated_effort && (
        <p className="text-2xs text-muted-foreground">
          Estimated effort: <span className="text-foreground">{skill.estimated_effort}</span>
        </p>
      )}
    </div>
  )
}

function SoftSkillCard({ skill }: { skill: SoftSkillRecommendation }) {
  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-foreground">{skill.skill}</p>
        <div className="flex items-center gap-1.5 shrink-0">
          {skill.gap_level && (
            <span className="text-2xs text-muted-foreground">{gapLabels[skill.gap_level] ?? skill.gap_level}</span>
          )}
          <PriorityTag priority={skill.priority} />
        </div>
      </div>
      {skill.why && <p className="text-xs text-muted-foreground whitespace-pre-wrap">{skill.why}</p>}
      <BulletList title="What to improve" items={skill.what_to_improve} />
      <BulletList title="How to practice" items={skill.how_to_practice} />
    </div>
  )
}

function BulletList({ title, items }: { title: string; items: string[] }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{title}</p>
      <ul className="space-y-0.5">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-foreground flex gap-1.5">
            <span className="shrink-0">•</span>
            <span className="break-words">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function PreparationPlan({ applicationId, preparation, generating, onGenerate }: PreparationPlanProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Lightning className="w-4 h-4 text-amber-500" />
          <p className="text-xs font-medium text-foreground">Preparation Plan</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="h-7 gap-1 text-xs"
          onClick={onGenerate}
          disabled={generating}
        >
          {generating ? <CircleNotch className="w-3.5 h-3.5 animate-spin" /> : <Lightning className="w-3.5 h-3.5" />}
          {preparation ? 'Regenerate' : 'Generate'}
        </Button>
      </div>

      {!preparation && !generating && (
        <p className="text-xs text-muted-foreground">
          No preparation plan yet. Generate a tailored skill plan from the job analysis and your profile.
        </p>
      )}

      {generating && !preparation && (
        <p className="text-xs text-muted-foreground">Generating your preparation plan…</p>
      )}

      {preparation && (
        <>
          <div className="flex items-center gap-2 text-2xs text-muted-foreground">
            <span>Version {preparation.version}</span>
            {preparation.created_at && (
              <>
                <span>·</span>
                <span>
                  Generated <DateTime value={preparation.created_at} />
                </span>
              </>
            )}
          </div>
          {preparation.hard_skills.length > 0 && (
            <div className="space-y-2">
              <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">Hard skills</p>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
                {preparation.hard_skills.map((skill, i) => (
                  <HardSkillCard key={i} skill={skill} />
                ))}
              </div>
            </div>
          )}
          {preparation.soft_skills.length > 0 && (
            <div className="space-y-2">
              <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">Soft skills</p>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
                {preparation.soft_skills.map((skill, i) => (
                  <SoftSkillCard key={i} skill={skill} />
                ))}
              </div>
            </div>
          )}
          {preparation.hard_skills.length === 0 && preparation.soft_skills.length === 0 && (
            <p className="text-xs text-muted-foreground">This plan has no recommendations yet.</p>
          )}
        </>
      )}
    </div>
  )
}
