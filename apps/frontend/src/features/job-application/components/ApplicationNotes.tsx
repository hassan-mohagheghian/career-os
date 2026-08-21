'use client'

import { useState } from 'react'
import { Note, Plus, Trash } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Textarea } from '@/shared/ui/textarea'
import DateTime from '@/shared/components/DateTime'
import type { ApplicationDetail } from '@/entities/application/types'
import { useAddNoteMutation, useDeleteNoteMutation } from '@/entities/application/hooks'

interface ApplicationNotesProps {
  application: ApplicationDetail
}

export function ApplicationNotes({ application }: ApplicationNotesProps) {
  const [content, setContent] = useState('')
  const addNote = useAddNoteMutation()
  const deleteNote = useDeleteNoteMutation()

  const handleAdd = () => {
    const trimmed = content.trim()
    if (!trimmed || addNote.isPending) return
    addNote.mutate(
      { applicationId: application.id, input: { content: trimmed } },
      {
        onSuccess: () => setContent(''),
        onError: () => {},
      },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-2">
      {application.notes.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No notes yet. Use notes to track your application activity in your own words.
        </p>
      )}

      <ul className="divide-y divide-border/40">
        {application.notes.map((note) => (
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
          placeholder="What happened? (call, email, interview impression, decision…)"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
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
