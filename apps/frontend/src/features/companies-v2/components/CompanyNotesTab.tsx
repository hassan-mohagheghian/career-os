import { useState } from 'react'
import { Note, Plus, PencilSimple, Trash, Link, Check, X, ArrowSquareOut, Spinner } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { companyApi } from '@/entities/company/api'

export default function CompanyNotesTab({ company, onUpdate }: { company: any; onUpdate?: any }) {
  const [notes, setNotes] = useState(() => {
    if (Array.isArray(company.notes)) return company.notes
    if (typeof company.notes === 'string') { try { return JSON.parse(company.notes) } catch { return [] } }
    return []
  })
  const [links, setLinks] = useState(company.links || [])
  const [noteInput, setNoteInput] = useState('')
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null)
  const [editNoteContent, setEditNoteContent] = useState('')
  const [saving, setSaving] = useState(false)

  // Link form state
  const [showLinkForm, setShowLinkForm] = useState(false)
  const [linkUrl, setLinkUrl] = useState('')
  const [linkTitle, setLinkTitle] = useState('')
  const [linkDesc, setLinkDesc] = useState('')
  const [editingLinkId, setEditingLinkId] = useState<number | null>(null)

  // Links come from the company detail payload (single API call), no separate fetch.
  // Notes CRUD
  const refreshNotes = async () => {
    try {
      const data = await companyApi.listNotes(company.id)
      setNotes(Array.isArray(data) ? data.map(n => ({ id: n.id, content: n.content })) : [])
    } catch { setNotes([]) }
  }

  const addNote = async () => {
    if (!noteInput.trim()) return
    setSaving(true)
    try {
      const data = await companyApi.addNote(company.id, { content: noteInput.trim() })
      onUpdate?.(data)
      setNoteInput('')
      await refreshNotes()
    } finally { setSaving(false) }
  }

  const updateNote = async (noteId: number) => {
    if (!editNoteContent.trim()) return
    setSaving(true)
    try {
      const data = await companyApi.updateNote(company.id, noteId, { content: editNoteContent.trim() })
      onUpdate?.(data)
      setEditingNoteId(null)
      setEditNoteContent('')
      await refreshNotes()
    } finally { setSaving(false) }
  }

  const deleteNote = async (noteId: number) => {
    setSaving(true)
    try {
      await companyApi.deleteNote(company.id, noteId)
      onUpdate?.({ status: 'deleted' })
      await refreshNotes()
    } finally { setSaving(false) }
  }

  // Links CRUD
  const addLink = async () => {
    if (!linkUrl.trim()) return
    setSaving(true)
    try {
      const data = await companyApi.addLink(company.id, { url: linkUrl.trim(), title: linkTitle.trim(), description: linkDesc.trim() })
      setLinks(prev => [data, ...prev])
      setLinkUrl('')
      setLinkTitle('')
      setLinkDesc('')
      setShowLinkForm(false)
    } finally { setSaving(false) }
  }

  const updateLink = async (linkId: number) => {
    setSaving(true)
    try {
      const data = await companyApi.updateLink(company.id, linkId, { url: linkUrl.trim(), title: linkTitle.trim(), description: linkDesc.trim() })
      setLinks(prev => prev.map(l => l.id === linkId ? data : l))
      setEditingLinkId(null)
      setLinkUrl('')
      setLinkTitle('')
      setLinkDesc('')
      setShowLinkForm(false)
    } finally { setSaving(false) }
  }

  const deleteLink = async (linkId: number) => {
    setSaving(true)
    try {
      await companyApi.deleteLink(company.id, linkId)
      setLinks(prev => prev.filter(l => l.id !== linkId))
    } finally { setSaving(false) }
  }

  const startEditLink = (link) => {
    setEditingLinkId(link.id)
    setLinkUrl(link.url)
    setLinkTitle(link.title || '')
    setLinkDesc(link.description || '')
    setShowLinkForm(true)
  }

  const cancelLinkForm = () => {
    setEditingLinkId(null)
    setLinkUrl('')
    setLinkTitle('')
    setLinkDesc('')
    setShowLinkForm(false)
  }

  return (
    <div className="space-y-4">
      {/* Section 1: Notes */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Note className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold">Company Notes</span>
          <Badge variant="secondary" className="text-2xs">{notes.length}</Badge>
        </div>
        <p className="text-2xs text-muted-foreground mb-2">
          Add notes about this company — research, observations, interview notes, culture info.
        </p>

        {/* Add note */}
        <div className="flex gap-1 mb-2">
          <textarea
            value={noteInput}
            onChange={e => setNoteInput(e.target.value)}
            placeholder="Add a note (any information about the company)..."
            rows={2}
            className="flex-1 rounded border text-xs px-2 py-1.5 bg-muted resize-none"
          />
        </div>
        <div className="flex justify-end mb-2">
          <Button onClick={addNote} disabled={saving || !noteInput.trim()} size="sm" className="h-6 px-2 text-2xs">
            <Plus className="w-2.5 h-2.5 mr-1" /> Add Note
          </Button>
        </div>

        {/* Notes list */}
        <div className="space-y-1 max-h-60 overflow-y-auto">
          {notes.length === 0 && (
            <div className="text-center py-3 text-2xs text-muted-foreground">No notes yet.</div>
          )}
          {notes.map((n) => {
            const isEditing = editingNoteId === n.id
            return (
              <div key={n.id} className="group rounded border bg-muted/50 px-2 py-1.5 text-xs">
                {isEditing ? (
                  <div className="space-y-1">
                    <textarea
                      value={editNoteContent}
                      onChange={e => setEditNoteContent(e.target.value)}
                      rows={3}
                      className="w-full rounded border text-xs px-2 py-1.5 bg-background resize-none"
                      autoFocus
                    />
                    <div className="flex justify-end gap-1">
                      <Button size="sm" variant="ghost" className="h-5 px-1.5 text-2xs" onClick={() => updateNote(n.id)}>
                        <Check className="w-2.5 h-2.5 mr-0.5" /> Save
                      </Button>
                      <Button size="sm" variant="ghost" className="h-5 px-1.5 text-2xs" onClick={() => { setEditingNoteId(null); setEditNoteContent('') }}>
                        <X className="w-2.5 h-2.5" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-1">
                    <Note className="w-2.5 h-2.5 text-muted-foreground mt-0.5 shrink-0" />
                    <span className="flex-1 min-w-0 whitespace-pre-wrap break-all">{n.content}</span>
                    <div className="flex items-center gap-0 shrink-0 opacity-0 group-hover:opacity-100 transition">
                      <button onClick={() => { setEditingNoteId(n.id); setEditNoteContent(n.content) }}
                        className="p-0.5 text-muted-foreground hover:text-foreground">
                        <PencilSimple className="w-2.5 h-2.5" />
                      </button>
                      <button onClick={() => deleteNote(n.id)}
                        className="p-0.5 text-muted-foreground hover:text-destructive">
                        <Trash className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t" />

      {/* Section 2: Links */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Link className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Company Links</span>
            <Badge variant="secondary" className="text-2xs">{links.length}</Badge>
          </div>
          {!showLinkForm && (
            <Button onClick={() => setShowLinkForm(true)} size="sm" variant="ghost" className="h-5 px-1.5 text-2xs">
              <Plus className="w-2.5 h-2.5 mr-0.5" /> Add Link
            </Button>
          )}
        </div>
        <p className="text-2xs text-muted-foreground mb-2">
          Add company pages, careers, blog posts, documentation, LinkedIn profiles.
        </p>

        {/* Add/Edit Link Form */}
        {showLinkForm && (
          <Card className="p-2 mb-2 space-y-1.5">
            <input
              type="url"
              value={linkUrl}
              onChange={e => setLinkUrl(e.target.value)}
              placeholder="URL (https://...)"
              className="w-full h-6 rounded border text-xs px-2 bg-muted"
              autoFocus
            />
            <div className="flex items-center gap-1">
              {['LinkedIn', 'Website', 'Careers', 'GitHub'].map(label => (
                <button key={label} type="button"
                  onClick={() => setLinkTitle(linkTitle === label ? '' : label)}
                  className={cn("h-5 px-1.5 rounded text-2xs border transition-colors",
                    linkTitle === label
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:bg-muted"
                  )}>{label}</button>
              ))}
              <input
                type="text"
                value={linkTitle}
                onChange={e => setLinkTitle(e.target.value)}
                placeholder="Custom title"
                className="flex-1 h-5 rounded border text-xs px-2 bg-muted"
              />
            </div>
            <input
              type="text"
              value={linkDesc}
              onChange={e => setLinkDesc(e.target.value)}
              placeholder="Description (optional)"
              className="w-full h-6 rounded border text-xs px-2 bg-muted"
            />
            <div className="flex justify-end gap-1">
              <Button size="sm" variant="ghost" className="h-5 px-1.5 text-2xs"
                onClick={() => editingLinkId ? updateLink(editingLinkId) : addLink()}
                disabled={saving || !linkUrl.trim()}>
                <Check className="w-2.5 h-2.5 mr-0.5" /> {editingLinkId ? 'Update' : 'Add'}
              </Button>
              <Button size="sm" variant="ghost" className="h-5 px-1.5 text-2xs" onClick={cancelLinkForm}>
                <X className="w-2.5 h-2.5" />
              </Button>
            </div>
          </Card>
        )}

        {/* Links list */}
        <div className="space-y-1 max-h-60 overflow-y-auto">
          {links.length === 0 && !showLinkForm && (
            <div className="text-center py-3 text-2xs text-muted-foreground">No links yet.</div>
          )}
          {links.map((link) => (
            <div key={link.id} className="group flex items-start gap-1.5 rounded border bg-muted/50 px-2 py-1.5 text-xs">
              <Link className="w-2.5 h-2.5 text-primary mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <a href={link.url} target="_blank" rel="noreferrer" className="text-primary hover:underline break-all">{link.url}</a>
                {link.title && <div className="text-muted-foreground truncate">{link.title}</div>}
                {link.description && <div className="text-2xs text-muted-foreground truncate">{link.description}</div>}
                <div className="flex items-center gap-1 mt-0.5">
                  <Badge variant={link.status === 'processed' ? 'default' : link.status === 'failed' ? 'destructive' : 'secondary'}
                    className="text-2xs px-1 py-0">
                    {link.status === 'processed' ? 'Processed' : link.status === 'failed' ? 'Failed' : 'Pending'}
                  </Badge>
                </div>
              </div>
              <div className="flex items-center gap-0 shrink-0 opacity-0 group-hover:opacity-100 transition">
                <a href={link.url} target="_blank" rel="noreferrer" className="p-0.5 text-muted-foreground hover:text-foreground">
                  <ArrowSquareOut className="w-2.5 h-2.5" />
                </a>
                <button onClick={() => startEditLink(link)}
                  className="p-0.5 text-muted-foreground hover:text-foreground">
                  <PencilSimple className="w-2.5 h-2.5" />
                </button>
                <button onClick={() => deleteLink(link.id)}
                  className="p-0.5 text-muted-foreground hover:text-destructive">
                  <Trash className="w-2.5 h-2.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
