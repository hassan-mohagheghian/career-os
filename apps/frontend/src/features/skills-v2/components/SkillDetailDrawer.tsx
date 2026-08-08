'use client'

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Star, PencilSimple, Trash, Code, Scissors,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import type { SkillListItem } from '@/entities/skill/types'
import { CategoryBadges, OriginBadge } from './SkillRow'

interface SkillDetailDrawerProps {
  skillId: number | null
  skill: SkillListItem | null
  onOpenChange: (id: number | null) => void
  onEdit: (id: number) => void
  onDelete: (id: number) => void
  onBreakDown: (id: number) => void
}

export function SkillDetailDrawer({
  skillId,
  skill,
  onOpenChange,
  onEdit,
  onDelete,
  onBreakDown,
}: SkillDetailDrawerProps) {
  const open = !!skill && !!skillId

  if (!skill) return null

  const confidence = skill.confidence != null ? Math.round(skill.confidence * 100) : null
  const demand = skill.market_relevance != null ? Math.round(skill.market_relevance * 100) : null

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onOpenChange(null) }}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between pl-4 pr-14 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5 text-primary shrink-0" />
            <span className="truncate">{skill.name}</span>
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
        <ScrollArea className="flex-1 min-h-0">
          <div className="px-4 py-3 space-y-4">
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

            {(skill.categories?.length > 0 || skill.category) && (
              <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
                <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Categories</p>
                <CategoryBadges categories={skill.categories} fallback={skill.category} />
              </div>
            )}

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
          </div>
        </ScrollArea>
        <div className="flex items-center justify-end gap-2 border-t border-border/40 px-4 py-3 shrink-0">
          <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs text-muted-foreground" onClick={() => skillId != null && onBreakDown(skillId)}>
            <Scissors className="w-3 h-3" /> Break down
          </Button>
          <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs text-destructive" onClick={() => skillId != null && onDelete(skillId)}>
            <Trash className="w-3 h-3" /> Delete
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
