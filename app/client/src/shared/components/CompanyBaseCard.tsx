import { useState } from 'react'
import {
  Globe, CheckCircle, Brain, Warning, LinkSimple, Copy,
  Note, Link, PencilSimple, Plus, X, Check
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Progress } from '@/shared/ui/progress'
import ProcessingCardFrame from './ProcessingCardFrame'
import StepProgress from './StepProgress'
import CardActions from './CardActions'

const STEPS = [
  { key: 'fetch', icon: <Globe className="w-3 h-3" />, label: 'Fetch content' },
  { key: 'extract', icon: <Brain className="w-3 h-3" />, label: 'Extract info' },
  { key: 'analyze', icon: <Brain className="w-3 h-3" />, label: 'Analyze company' },
  { key: 'save', icon: <CheckCircle className="w-3 h-3" />, label: 'Save to DB' },
  { key: 'done', icon: <CheckCircle className="w-3 h-3" />, label: 'Complete' },
]

const STEP_KEYS = ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done']

function setToast(msg: string) {
  window.dispatchEvent(new CustomEvent('toast', { detail: msg }))
}

interface CompanyBaseCardProps {
  item: any
  dotColor: string
  statusText: React.ReactNode
  disabled?: boolean
  onDelete?: () => void
  onProcess?: () => void
  onCancel?: () => void
  onReset?: () => void
}

export default function CompanyBaseCard({
  item, dotColor, statusText, disabled = false,
  onDelete, onProcess, onCancel, onReset,
}: CompanyBaseCardProps) {
  const [editing, setEditing] = useState(false)
  const [editNotes, setEditNotes] = useState<any[]>([])
  const [editLinks, setEditLinks] = useState<any[]>([])
  const [newNote, setNewNote] = useState('')
  const [newLinkUrl, setNewLinkUrl] = useState('')
  const [newLinkTitle, setNewLinkTitle] = useState('')
  const [saving, setSaving] = useState(false)

  const vals = STEP_KEYS.map((k: string) => (item as any)[k])
  const done = vals.filter((s: number) => s === 1).length
  const isProcessing = item.status === 'processing'
  const nextStep = isProcessing ? vals.findIndex((s: number) => s !== 1) : -1
  const progress = (done / STEPS.length) * 100
  const isPending = item.status === 'pending'

  const handleCopySession = () => {
    if (item.session_id) {
      navigator.clipboard.writeText(item.session_id)
      setToast('Session ID copied')
    }
  }

  const startEdit = () => {
    const parseArr = (v: any) =>
      Array.isArray(v) ? [...v]
      : typeof v === 'string' ? (() => { try { return JSON.parse(v) } catch { return [] } })()
      : []
    setEditNotes(parseArr(item.notes))
    setEditLinks(parseArr(item.links))
    setEditing(true)
  }

  const cancelEdit = () => {
    setEditing(false)
    setNewNote('')
    setNewLinkUrl('')
    setNewLinkTitle('')
  }

  const saveEdit = async () => {
    setSaving(true)
    try {
      await fetch(`/api/pending-companies/${item.id}/notes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: editNotes }),
      })
      await fetch(`/api/pending-companies/${item.id}/links`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ links: editLinks }),
      })
      item.notes = editNotes
      item.links = editLinks
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const addEditNote = () => {
    if (!newNote.trim()) return
    setEditNotes(prev => [...prev, { type: 'text', content: newNote.trim() }])
    setNewNote('')
  }

  const removeEditNote = (idx: number) => {
    setEditNotes(prev => prev.filter((_, i) => i !== idx))
  }

  const addEditLink = () => {
    if (!newLinkUrl.trim()) return
    let url = newLinkUrl.trim()
    if (!url.startsWith('http')) url = 'https://' + url
    setEditLinks(prev => [...prev, { url, title: newLinkTitle.trim() }])
    setNewLinkUrl('')
    setNewLinkTitle('')
  }

  const removeEditLink = (idx: number) => {
    setEditLinks(prev => prev.filter((_, i) => i !== idx))
  }

  const hasNotes = Array.isArray(item.notes) && item.notes.length > 0
  const hasLinks = Array.isArray(item.links) && item.links.length > 0

  return (
    <ProcessingCardFrame status={item.status}>
      {/* Row 1: Status dot + badges + title */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <div className={cn('w-2 h-2 rounded-full shrink-0', dotColor)} />
        {item.source === 'reprocess' && <span className="text-3xs px-0.5 rounded bg-secondary text-secondary-foreground shrink-0">R</span>}
        <span className="text-2xs font-bold truncate min-w-0">{item.company_name || 'Processing...'}</span>
      </div>

      {/* Row 2: Step icons */}
      <StepProgress steps={STEPS} values={vals} nextStep={nextStep} />

      {/* Row 3: Progress */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <span className="text-2xs font-semibold text-muted-foreground shrink-0">{done}/{STEPS.length}</span>
        <Progress value={progress} className="h-0.5 flex-1 min-w-0" />
      </div>

      {/* Row 3.5: Notes & links */}
      {editing ? (
        <div className="mb-1 p-1.5 rounded border border-primary/30 bg-primary/5 space-y-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-2xs font-bold text-primary">Edit Notes & Links</span>
            <div className="flex gap-0.5">
              <Button size="icon" className="h-4 w-4" onClick={saveEdit} disabled={saving} title="Save">
                <CheckCircle className="w-2.5 h-2.5" />
              </Button>
              <Button size="icon" variant="ghost" className="h-4 w-4" onClick={cancelEdit} title="Cancel">
                <X className="w-2.5 h-2.5" />
              </Button>
            </div>
          </div>
          <div className="space-y-0.5">
            {editNotes.map((n: any, i: number) => (
              <div key={i} className="flex items-center gap-1 group/note min-w-0">
                <Note className="w-2 h-2 text-muted-foreground shrink-0" />
                <span className="text-2xs truncate flex-1 min-w-0">{(n.content || '').slice(0, 40)}</span>
                <button onClick={() => removeEditNote(i)} className="opacity-0 group-hover/note:opacity-100 text-destructive shrink-0"><X className="w-2 h-2" /></button>
              </div>
            ))}
            <div className="flex gap-0.5">
              <input value={newNote} onChange={e => setNewNote(e.target.value)} onKeyDown={e => e.key === 'Enter' && addEditNote()}
                placeholder="Add note..." className="flex-1 h-4 rounded border text-2xs px-1 bg-background min-w-0" />
              <Button size="icon" variant="ghost" className="h-4 w-4 shrink-0" onClick={addEditNote} disabled={!newNote.trim()}>
                <Plus className="w-2 h-2" />
              </Button>
            </div>
          </div>
          <div className="space-y-0.5">
            {editLinks.map((l: any, i: number) => (
              <div key={i} className="flex items-center gap-1 group/link min-w-0">
                <Link className="w-2 h-2 text-primary shrink-0" />
                <span className="text-2xs truncate flex-1 min-w-0">{l.title || l.url?.slice(0, 40) || ''}</span>
                <button onClick={() => removeEditLink(i)} className="opacity-0 group-hover/link:opacity-100 text-destructive shrink-0"><X className="w-2 h-2" /></button>
              </div>
            ))}
            <div className="flex gap-0.5">
              <input value={newLinkUrl} onChange={e => setNewLinkUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && addEditLink()}
                placeholder="URL..." className="flex-1 h-4 rounded border text-2xs px-1 bg-background min-w-0" />
              <input value={newLinkTitle} onChange={e => setNewLinkTitle(e.target.value)} onKeyDown={e => e.key === 'Enter' && addEditLink()}
                placeholder="Title" className="w-14 h-4 rounded border text-2xs px-1 bg-background shrink-0" />
              <Button size="icon" variant="ghost" className="h-4 w-4 shrink-0" onClick={addEditLink} disabled={!newLinkUrl.trim()}>
                <Plus className="w-2 h-2" />
              </Button>
            </div>
          </div>
        </div>
      ) : hasNotes || hasLinks ? (
        <div className="mb-1 min-w-0 space-y-px">
          {hasNotes && (
            <div className="flex items-center gap-1 min-w-0">
              <Note className="w-2 h-2 text-muted-foreground shrink-0" />
              <div className="text-2xs text-muted-foreground truncate min-w-0 leading-tight">
                {item.notes.length} note{item.notes.length !== 1 ? 's' : ''}: {item.notes.slice(0, 2).map((n: any) => (n.content || '').slice(0, 25)).join('; ')}{item.notes.length > 2 ? '...' : ''}
              </div>
            </div>
          )}
          {hasLinks && (
            <div className="flex items-center gap-1 min-w-0">
              <Link className="w-2 h-2 text-primary shrink-0" />
              <div className="text-2xs text-muted-foreground truncate min-w-0 leading-tight">
                {item.links.length} link{item.links.length !== 1 ? 's' : ''}: {item.links.slice(0, 2).map((l: any) => l.title || l.url?.slice(0, 25) || '').join(', ')}{item.links.length > 2 ? '...' : ''}
              </div>
            </div>
          )}
          {isPending && (
            <div className="flex justify-end">
              <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 opacity-0 group-hover/card:opacity-100" onClick={startEdit} title="Edit notes & links">
                <PencilSimple className="w-2 h-2" />
              </Button>
            </div>
          )}
        </div>
      ) : isPending ? (
        <div className="mb-1">
          <Button variant="ghost" size="sm" className="h-4 px-1 text-2xs text-muted-foreground hover:text-primary opacity-0 group-hover/card:opacity-100" onClick={startEdit}>
            <Plus className="w-2 h-2 mr-0.5" /> Add notes/links
          </Button>
        </div>
      ) : null}

      {/* Row 4: URL + status + session + actions */}
      <div className="flex items-center gap-1 min-w-0">
        {item.input_text && item.input_type === 'url' && (
          <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0" onClick={(e) => { e.stopPropagation(); window.open(item.input_text, '_blank') }} title="Open URL">
            <LinkSimple className="w-1.5 h-1.5 text-primary" />
          </Button>
        )}
        <span className="text-2xs truncate flex-1 min-w-0 text-muted-foreground">
          {statusText}
          {item.session_id ? (
            <button onClick={(e) => { e.stopPropagation(); handleCopySession() }} className="text-3xs text-muted-foreground hover:text-foreground font-mono ml-1" title={`Click to copy: ${item.session_id}`}>
              {item.session_id.slice(0, 6)}...
            </button>
          ) : item.status !== 'done' && item.status !== 'completed' ? (
            <span className="text-3xs text-muted-foreground/50 font-mono ml-1">no_session_id</span>
          ) : null}
        </span>
        <CardActions
          status={item.status}
          size="sm"
          disabled={disabled}
          error={item.error}
          onDelete={onDelete}
          onProcess={onProcess}
          onCancel={onCancel}
          onReset={onReset}
        />
      </div>
    </ProcessingCardFrame>
  )
}
