'use client'

import { useEffect, useState } from 'react'
import { CircleNotch, Scissors, Warning } from '@phosphor-icons/react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'

interface BreakdownSkillDialogProps {
  skill: { id: number; name: string } | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onBreakDown: (childNames: string[]) => void
  pending: boolean
}

export function BreakdownSkillDialog({ skill, open, onOpenChange, onBreakDown, pending }: BreakdownSkillDialogProps) {
  const [childrenInput, setChildrenInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setChildrenInput('')
      setError(null)
    }
  }, [open])

  const childNames = childrenInput
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const handleBreakDown = () => {
    if (!skill) return
    if (childNames.length < 2) {
      setError('List at least two atomic skills, separated by commas.')
      return
    }
    setError(null)
    onBreakDown(childNames)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader className="space-y-1.5">
          <DialogTitle className="flex items-center gap-2">
            <Scissors className="w-5 h-5 text-primary" />
            Break down {skill?.name ?? 'skill'}
          </DialogTitle>
          <DialogDescription>
            Split a composite skill into its atomic children. Each child becomes a separate skill,
            this skill&apos;s mentions are duplicated onto every child, and this skill is hidden.
            Extraction then surfaces the children whenever a job requires this composite.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1">
          <Input
            value={childrenInput}
            onChange={(e) => setChildrenInput(e.target.value)}
            placeholder="e.g. SQL, NoSQL, GraphQL"
            aria-label="Atomic child skills, comma-separated"
          />
          {error && (
            <p className="flex items-center gap-1 text-2xs text-destructive">
              <Warning className="w-3 h-3" /> {error}
            </p>
          )}
        </div>

        <DialogFooter className="flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleBreakDown} disabled={!skill || pending} className="gap-1">
            {pending ? <CircleNotch className="w-3.5 h-3.5 animate-spin" /> : <Scissors className="w-3.5 h-3.5" />}
            {pending ? 'Breaking down...' : 'Break down'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
