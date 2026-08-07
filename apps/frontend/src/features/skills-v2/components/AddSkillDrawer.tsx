'use client'

import { useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import { Plus, Warning, CircleNotch, TagSimple } from '@phosphor-icons/react'
import { SKILL_CATEGORIES } from '@/entities/skill/types'

interface AddSkillDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: { name: string; level: number; roles: string; path: string; category: string }) => void
  submitting?: boolean
  error?: string | null
}

function Field({
  label,
  required = false,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1">
      <label className="flex items-center gap-0.5 text-xs text-muted-foreground">
        <span>{label}</span>
        {required && <span className="text-destructive">*</span>}
        {!required && <span className="text-muted-foreground/60">(optional)</span>}
      </label>
      {children}
    </div>
  )
}

export default function AddSkillDrawer({
  open,
  onOpenChange,
  onSubmit,
  submitting = false,
  error = null,
}: AddSkillDrawerProps) {
  const [name, setName] = useState('')
  const [level, setLevel] = useState(1)
  const [category, setCategory] = useState('')
  const [roles, setRoles] = useState('')
  const [path, setPath] = useState('')

  const canSubmit = name.trim().length > 0

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next)
    if (!next) {
      setName('')
      setLevel(1)
      setCategory('')
      setRoles('')
      setPath('')
    }
  }

  const handleSubmit = () => {
    if (!canSubmit || submitting) return
    onSubmit({
      name: name.trim(),
      level,
      roles: roles.trim(),
      path: path.trim(),
      category,
    })
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[480px] p-0 flex flex-col h-full">
        <SheetHeader className="shrink-0 flex flex-row items-center justify-between px-4 py-3 border-b border-border/40">
          <SheetTitle className="text-sm font-semibold flex items-center gap-1.5">
            <Plus className="w-3.5 h-3.5" /> Add Skill
          </SheetTitle>
        </SheetHeader>
        <div className="flex-1 min-h-0">
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto space-y-3 px-4 py-4">
              <Field label="Name" required>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Kubernetes" autoFocus />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Level">
                  <Select value={String(level)} onValueChange={(v) => setLevel(Number(v))}>
                    <SelectTrigger className="h-8 text-xs">{level}</SelectTrigger>
                    <SelectContent position="popper">
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                        <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Category">
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="h-8 text-xs">
                      <span className="truncate">{category || 'Select'}</span>
                    </SelectTrigger>
                    <SelectContent position="popper">
                      {SKILL_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
              </div>
              <Field label="Relevant Roles">
                <Input value={roles} onChange={(e) => setRoles(e.target.value)} placeholder="backend engineer, data engineer" />
              </Field>
              <Field label="Path">
                <Textarea
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  placeholder="Where this skill fits your career path..."
                  className="min-h-[70px] text-xs resize-none"
                />
              </Field>

              {error && (
                <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
                  <Warning className="w-3.5 h-3.5 shrink-0" />
                  {error}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t px-4 shrink-0">
              <Button variant="outline" size="sm" onClick={() => handleOpenChange(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button variant="default" size="sm" disabled={!canSubmit || submitting} onClick={handleSubmit}>
                {submitting ? <CircleNotch className="w-3 h-3 animate-spin" /> : <TagSimple className="w-3 h-3" />}
                {submitting ? 'Adding...' : 'Add Skill'}
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
