'use client'

import { Button } from '@/shared/ui/button'
import { Plus, Code, ArrowsClockwise } from '@phosphor-icons/react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'

interface SkillsHeaderProps {
  total: number
  loadedCount: number
  onAddSkill: () => void
  onRefresh?: () => void
  isRefreshing?: boolean
}

export function SkillsHeader({ total, loadedCount, onAddSkill, onRefresh, isRefreshing }: SkillsHeaderProps) {
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
        {onRefresh && (
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  onClick={onRefresh}
                  disabled={isRefreshing}
                  aria-label="Refresh skills"
                >
                  <ArrowsClockwise className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Refresh skills</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </div>
  )
}
