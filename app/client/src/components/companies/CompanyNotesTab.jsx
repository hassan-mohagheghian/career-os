import { useState } from 'react'
import { Note, Plus, PencilSimple, Trash, Link, Check, X } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function CompanyNotesTab({ company, onUpdate }) {
  const [notes, setNotes] = useState(() => {
    if (Array.isArray(company.notes)) return company.notes
    if (typeof company.notes === 'string') { try { return JSON.parse(company.notes) } catch { return [] } }
    return []
  })
  const [input, setInput] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const addNote = async () => {
    if (!input.trim()) return
    setSaving(true)
    try {
      const res = await fetch(`/api/companies/${company.id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'auto', content: input.trim() })
      })
      const data = await res.json()
      setNotes(data)
      onUpdate?.(data)
      setInput('')
    } finally { setSaving(false) }
  }

  const updateNote = async (noteId) => {
    if (!editContent.trim()) return
    setSaving(true)
    try {
      const res = await fetch(`/api/companies/${company.id}/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent.trim() })
      })
      const data = await res.json()
      setNotes(data)
      onUpdate?.(data)
      setEditingId(null)
      setEditContent('')
    } finally { setSaving(false) }
  }

  const deleteNote = async (noteId) => {
    setSaving(true)
    try {
      const res = await fetch(`/api/companies/${company.id}/notes/${noteId}`, { method: 'DELETE' })
      const data = await res.json()
      setNotes(data)
      onUpdate?.(data)
    } finally { setSaving(false) }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Note className="w-4 h-4 text-primary" />
        <span className="text-xs font-semibold">Company Notes</span>
        <Badge variant="secondary" className="text-[0.5rem]">{notes.length}</Badge>
      </div>
      <p className="text-[0.6rem] text-muted-foreground">
        Add notes about this company. These are used when reprocessing to generate better intelligence.
      </p>

      {/* Add note input */}
      <div className="flex gap-1">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addNote()}
          placeholder="Add a note (URL, description, anything)..."
          className="flex-1 h-7 rounded border text-xs px-2 bg-muted"
        />
        <Button onClick={addNote} disabled={saving || !input.trim()} size="sm" className="h-7 px-2">
          <Plus className="w-3 h-3" />
        </Button>
      </div>

      {/* Notes list */}
      <div className="space-y-1 max-h-60 overflow-y-auto">
        {notes.length === 0 && (
          <div className="text-center py-4 text-xs text-muted-foreground">No notes yet. Add one above.</div>
        )}
        {notes.map((n) => {
          const isUrl = n.type === 'url' || (n.content || '').startsWith('http')
          const isEditing = editingId === n.id
          return (
            <div key={n.id} className="group flex items-start gap-1 rounded border bg-muted/50 px-2 py-1.5 text-xs">
              <span className="shrink-0 mt-0.5">
                {isUrl ? <Link className="w-2.5 h-2.5 text-primary" /> : <Note className="w-2.5 h-2.5 text-muted-foreground" />}
              </span>
              {isEditing ? (
                <div className="flex-1 flex gap-1">
                  <input
                    type="text"
                    value={editContent}
                    onChange={e => setEditContent(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && updateNote(n.id)}
                    className="flex-1 h-6 rounded border text-xs px-1.5"
                    autoFocus
                  />
                  <Button size="sm" variant="ghost" className="h-6 w-6 px-0" onClick={() => updateNote(n.id)}>
                    <Check className="w-3 h-3 text-green-500" />
                  </Button>
                  <Button size="sm" variant="ghost" className="h-6 w-6 px-0" onClick={() => { setEditingId(null); setEditContent('') }}>
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              ) : (
                <span className="flex-1 min-w-0 break-all">
                  {isUrl ? (
                    <a href={n.content} target="_blank" rel="noreferrer" className="text-primary hover:underline">{n.content}</a>
                  ) : n.content}
                </span>
              )}
              {!isEditing && (
                <div className="flex items-center gap-0 shrink-0 opacity-0 group-hover:opacity-100 transition">
                  <button onClick={() => { setEditingId(n.id); setEditContent(n.content) }}
                    className="p-0.5 text-muted-foreground hover:text-foreground">
                    <PencilSimple className="w-2.5 h-2.5" />
                  </button>
                  <button onClick={() => deleteNote(n.id)}
                    className="p-0.5 text-muted-foreground hover:text-destructive">
                    <Trash className="w-2.5 h-2.5" />
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
