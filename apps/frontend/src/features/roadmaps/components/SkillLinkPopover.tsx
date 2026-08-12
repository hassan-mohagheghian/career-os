'use client'

import { useState } from 'react'
import { LinkSimple } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { useLinkSkillMutation } from '@/entities/roadmap/hooks'
import type { RoadmapMilestone, RoadmapTask } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/shared/ui/popover'

export function SkillLinkPopover({
  roadmapId,
  milestone,
  task,
}: {
  roadmapId: string
  milestone?: RoadmapMilestone
  task?: RoadmapTask
}) {
  const linkSkill = useLinkSkillMutation()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')

  const handleLink = () => {
    if (!name.trim()) return
    linkSkill.mutate(
      { skill_name: name.trim(), milestone_id: milestone?.id ?? null, task_id: task?.id ?? null },
      {
        onSuccess: () => {
          toast.success('Skill linked')
          setName('')
          setOpen(false)
        },
        onError: () => toast.error('Failed to link skill'),
      },
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          size="icon"
          variant="ghost"
          className="h-6 w-6"
          title={task ? 'Link skill to task' : 'Link skill to milestone'}
        >
          <LinkSimple className="w-3 h-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <p className="text-xs font-medium">Link a skill</p>
        <div className="flex flex-col gap-1.5">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Skill name (e.g. Kafka)"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleLink()
            }}
          />
          <Button size="sm" className="h-7 text-xs" onClick={handleLink} disabled={!name.trim() || linkSkill.isPending}>
            {linkSkill.isPending ? 'Linking...' : 'Link skill'}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}