'use client'

import { Button } from '@/shared/ui/button'
import { Plus, Code } from '@phosphor-icons/react'

interface SkillsHeaderProps {
  total: number
  loadedCount: number
  onAddSkill: () => void
}

export function SkillsHeader({ total, loadedCount, onAddSkill }: SkillsHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          <Code className="w-3.5 h-3.5" /> Skills ({total})
        </h1>
        <span className="text-2xs text-muted-foreground">
          Loaded {loadedCount} of {total} skills
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Button size="sm" className="h-7 text-xs gap-1.5" onClick={onAddSkill}>
          <Plus className="w-3.5 h-3.5" />
          Add Skill
        </Button>
      </div>
    </div>
  )
}
