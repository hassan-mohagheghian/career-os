'use client'

import { useEffect, useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Input } from '@/shared/ui/input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import { Badge } from '@/shared/ui/badge'
import { PencilSimple, Warning, Check, TagSimple, CircleNotch, Plus, X, GitMerge } from '@phosphor-icons/react'
import { skillApi } from '@/entities/skill/api'
import { SKILL_CATEGORIES } from '@/entities/skill/types'
import { useQueryClient } from '@tanstack/react-query'
import { MergeSkillDialog } from './MergeSkillDialog'

const SKILLS_KEY = 'skills-v2-infinite'

interface SkillEditDrawerProps {
  skillId: number | null
  onOpenChange: (id: number | null) => void
}

function Field({
  label,
  required = false,
  hint,
  children,
}: {
  label: string
  required?: boolean
  hint?: string
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
      {hint && <p className="text-2xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

export function SkillEditDrawer({ skillId, onOpenChange }: SkillEditDrawerProps) {
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [level, setLevel] = useState(1)
  const [category, setCategory] = useState('')
  const [roles, setRoles] = useState('')
  const [tagsInput, setTagsInput] = useState('')
  const [aliases, setAliases] = useState<string[]>([])
  const [newAlias, setNewAlias] = useState('')
  const [aliasBusy, setAliasBusy] = useState(false)
  const [mergeOpen, setMergeOpen] = useState(false)
  const [mergePending, setMergePending] = useState(false)

  const open = skillId != null

  useEffect(() => {
    if (skillId == null) return
    let active = true
    setLoading(true)
    setError(null)
    skillApi.get(skillId)
      .then((d) => {
        if (!active) return
        setName(d.name ?? '')
        setLevel(d.level ?? 1)
        setCategory(d.category ?? '')
        setRoles(d.roles ?? '')
        setTagsInput((d.tags ?? []).join(', '))
        setAliases(d.aliases ?? [])
      })
      .catch(() => active && setError('Unable to load skill details.'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [skillId])

  const handleSave = async () => {
    if (skillId == null) return
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    setSubmitting(true)
    setError(null)
    const payload = {
      name: name.trim(),
      level,
      category,
      roles: roles.trim(),
      tags: tagsInput.split(',').map((t) => t.trim()).filter(Boolean),
    }
    try {
      await skillApi.update(skillId, payload)
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] })
      onOpenChange(null)
    } catch {
      setError('Failed to save changes. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddAlias = async () => {
    if (skillId == null) return
    const alias = newAlias.trim()
    if (!alias || aliases.includes(alias)) return
    setAliasBusy(true)
    setError(null)
    try {
      const updated = await skillApi.addAlias(skillId, alias)
      setAliases(updated.aliases ?? [...aliases, alias])
      setNewAlias('')
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] })
    } catch {
      setError('Failed to add alias.')
    } finally {
      setAliasBusy(false)
    }
  }

  const handleRemoveAlias = async (alias: string) => {
    if (skillId == null) return
    setAliasBusy(true)
    setError(null)
    try {
      const updated = await skillApi.removeAlias(skillId, alias)
      setAliases(updated.aliases ?? aliases.filter((a) => a !== alias))
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] })
    } catch {
      setError('Failed to remove alias.')
    } finally {
      setAliasBusy(false)
    }
  }

  const handleMerge = async (targetId: number) => {
    if (skillId == null) return
    setMergePending(true)
    setError(null)
    try {
      await skillApi.merge(targetId, [skillId])
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] })
      onOpenChange(null)
    } catch {
      setError('Failed to merge skill.')
    } finally {
      setMergePending(false)
    }
  }

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onOpenChange(null) }}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col h-full">
        <SheetHeader className="shrink-0 flex flex-row items-center justify-between px-4 py-3 border-b border-border/40">
          <SheetTitle className="text-sm font-semibold flex items-center gap-1.5">
            <PencilSimple className="w-3.5 h-3.5" /> Edit Skill
          </SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0">
          {loading && (
            <div className="flex items-center justify-center h-40">
              <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
            </div>
          )}

          {!loading && error && (
            <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2 m-4">
              <Warning className="w-3.5 h-3.5 shrink-0" />
              {error}
            </div>
          )}

          {!loading && skillId != null && (
            <div className="space-y-3 px-4 py-4">
              <Field label="Name" required>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Level">
                  <Select value={String(level)} onValueChange={(v) => setLevel(Number(v))}>
                    <SelectTrigger className="h-8 text-xs">{level}</SelectTrigger>
                    <SelectContent>
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
                    <SelectContent>
                      {SKILL_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
              </div>
              <Field label="Relevant Roles">
                <Input value={roles} onChange={(e) => setRoles(e.target.value)} />
              </Field>
              <Field label="Tags" hint="Comma-separated">
                <div className="flex items-center gap-1">
                  <TagSimple className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  <Input value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="ai, ml, backend" />
                </div>
              </Field>

              <Field label="Aliases" hint="Other names for this skill (e.g. 'ReactJS' for 'React')">
                <div className="space-y-2">
                  {aliases.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {aliases.map((a) => (
                        <Badge key={a} variant="outline" className="gap-1 pr-1 text-2xs">
                          {a}
                          <button
                            type="button"
                            onClick={() => handleRemoveAlias(a)}
                            className="rounded-full p-0.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                            aria-label={`Remove alias ${a}`}
                            disabled={aliasBusy}
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-2xs text-muted-foreground">No aliases yet.</p>
                  )}
                  <div className="flex items-center gap-1">
                    <Input
                      value={newAlias}
                      onChange={(e) => setNewAlias(e.target.value)}
                      placeholder="Add alias..."
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddAlias() } }}
                    />
                    <Button type="button" size="icon" variant="outline" className="h-7 w-7 shrink-0" onClick={handleAddAlias} disabled={aliasBusy || !newAlias.trim()} aria-label="Add alias">
                      {aliasBusy ? <CircleNotch className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                    </Button>
                  </div>
                </div>
              </Field>

              <div className="pt-1">
                <Button variant="outline" size="sm" className="h-7 text-2xs gap-1" onClick={() => setMergeOpen(true)}>
                  <GitMerge className="w-3 h-3" /> Merge into another skill
                </Button>
              </div>

              {error && (
                <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
                  <Warning className="w-3.5 h-3.5 shrink-0" />
                  {error}
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        {!loading && skillId != null && (
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t shrink-0">
            <Button variant="outline" size="sm" onClick={() => onOpenChange(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="default" size="sm" onClick={handleSave} disabled={submitting}>
              {submitting ? <CircleNotch className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
              {submitting ? 'Saving...' : 'Save'}
            </Button>
          </div>
        )}
      </SheetContent>
      <MergeSkillDialog
        skill={skillId != null ? { id: skillId, name } : null}
        open={mergeOpen}
        onOpenChange={setMergeOpen}
        onMerge={handleMerge}
        pending={mergePending}
      />
    </Sheet>
  )
}
