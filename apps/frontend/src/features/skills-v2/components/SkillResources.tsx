'use client'

import { useState } from 'react'
import { Note, Plus, Trash, Link as LinkIcon } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Textarea } from '@/shared/ui/textarea'
import { Input } from '@/shared/ui/input'
import DateTime from '@/shared/components/DateTime'
import type { Skill, SkillListItem } from '@/entities/skill/types'
import {
  useAddSkillNoteMutation,
  useDeleteSkillNoteMutation,
  useAddSkillLinkMutation,
  useDeleteSkillLinkMutation,
} from '@/entities/skill/hooks'

interface SkillResourcesProps {
  skill: Skill | SkillListItem
}

export function SkillResources({ skill }: SkillResourcesProps) {
  const notes = skill.notes ?? []
  const links = skill.links ?? []

  return (
    <div className="space-y-4">
      <SkillNotes skillId={skill.id} notes={notes} />
      <SkillLinks skillId={skill.id} links={links} />
    </div>
  )
}

function SkillNotes({ skillId, notes }: { skillId: number; notes: Skill['notes'] }) {
  const [content, setContent] = useState('')
  const addNote = useAddSkillNoteMutation()
  const deleteNote = useDeleteSkillNoteMutation()

  const handleAdd = () => {
    const trimmed = content.trim()
    if (!trimmed || addNote.isPending) return
    addNote.mutate(
      { skillId, content: trimmed },
      { onSuccess: () => setContent('') },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">
        Notes
      </p>

      {notes.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No notes yet. Track your learning progress here.
        </p>
      )}

      <ul className="divide-y divide-border/40">
        {notes.map((note) => (
          <li key={note.id} className="flex items-start gap-2 py-1.5 group">
            <div className="flex-1 min-w-0 space-y-0.5">
              <p className="text-xs whitespace-pre-wrap break-words">{note.content}</p>
              {note.created_at && (
                <p className="text-2xs text-muted-foreground">
                  <DateTime value={note.created_at} />
                </p>
              )}
            </div>
            <button
              type="button"
              aria-label="Delete note"
              onClick={() => deleteNote.mutate(note.id)}
              className="text-muted-foreground/50 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            >
              <Trash className="w-3.5 h-3.5" />
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-2">
        <Textarea
          placeholder="What did you learn? What should you study next?"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          className="text-xs"
        />
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={handleAdd}
            disabled={!content.trim() || addNote.isPending}
          >
            {addNote.isPending ? (
              <Note className="w-3.5 h-3.5 animate-pulse" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            Add Note
          </Button>
        </div>
      </div>
    </div>
  )
}

function SkillLinks({ skillId, links }: { skillId: number; links: Skill['links'] }) {
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const addLink = useAddSkillLinkMutation()
  const deleteLink = useDeleteSkillLinkMutation()

  const handleAdd = () => {
    const t = title.trim()
    const u = url.trim()
    if (!t || !u || addLink.isPending) return
    addLink.mutate(
      { skillId, title: t, url: u },
      { onSuccess: () => { setTitle(''); setUrl('') } },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">
        Links
      </p>

      {links.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No links yet. Save documentation, tutorials, or references.
        </p>
      )}

      <ul className="divide-y divide-border/40">
        {links.map((link) => (
          <li key={link.id} className="flex items-center gap-2 py-1.5 group">
            <LinkIcon className="w-3 h-3 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <a
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium text-primary hover:underline truncate block"
              >
                {link.title}
              </a>
              <p className="text-2xs text-muted-foreground truncate">{link.url}</p>
            </div>
            <button
              type="button"
              aria-label="Delete link"
              onClick={() => deleteLink.mutate(link.id)}
              className="text-muted-foreground/50 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            >
              <Trash className="w-3.5 h-3.5" />
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-2">
        <Input
          placeholder="Title (e.g. Official Docs)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="text-xs h-7"
        />
        <Input
          placeholder="URL (https://...)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          className="text-xs h-7"
        />
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={handleAdd}
            disabled={!title.trim() || !url.trim() || addLink.isPending}
          >
            {addLink.isPending ? (
              <LinkIcon className="w-3.5 h-3.5 animate-pulse" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            Add Link
          </Button>
        </div>
      </div>
    </div>
  )
}
