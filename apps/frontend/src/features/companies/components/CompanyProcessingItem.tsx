import { useState } from 'react'
import {
  Check, Globe, CheckCircle, Brain, Warning, LinkSimple,
  Note, Link, PencilSimple, Plus, X
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Progress } from '@/shared/ui/progress'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/shared/ui/tooltip'
import CardActions from '@/shared/components/CardActions'

function setToast(msg) {
  window.dispatchEvent(new CustomEvent('toast', { detail: msg }))
}

const STEPS = [
  { key: 'fetch', icon: <Globe className="w-3 h-3" />, abbr: 'Fetch', label: 'Fetch content' },
  { key: 'extract', icon: <Brain className="w-3 h-3" />, abbr: 'Extract', label: 'Extract info' },
  { key: 'analyze', icon: <Brain className="w-3 h-3" />, abbr: 'Analyze', label: 'Analyze company' },
  { key: 'save', icon: <CheckCircle className="w-3 h-3" />, abbr: 'Save', label: 'Save to DB' },
  { key: 'done', icon: <CheckCircle className="w-3 h-3" />, abbr: 'Done', label: 'Complete' },
]

const STEP_KEYS = ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done']

function getStatus(item) {
  if (item.status === 'processed') return 'processed'
  if (item.status === 'failed') return 'failed'
  if (item.status === 'processing') {
    const vals = STEP_KEYS.map(k => item[k])
    const done = vals.filter(s => s === 1).length
    const labels = ['Fetching', 'Extracting', 'Analyzing', 'Saving', 'Done']
    return labels[Math.min(done, labels.length - 1)] || 'Processing'
  }
  if (item.status === 'queued') return 'Queued'
  if (item.status === 'pending') return 'Pending'
  return 'Created'
}

export default function CompanyProcessingItem({ item, onDelete, onProcess, onMoveToCreated, onPause, onReprocess }) {
  const [processing, setProcessing] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editNotes, setEditNotes] = useState([])
  const [editLinks, setEditLinks] = useState([])
  const [newNote, setNewNote] = useState('')
  const [newLinkUrl, setNewLinkUrl] = useState('')
  const [newLinkTitle, setNewLinkTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const statusKey = getStatus(item)
  const isDone = item.status === 'processed'
  const isFailed = item.status === 'failed'
  const isCancelled = item.status === 'cancelled'
  const isQueued = item.status === 'queued'
  const isPending = item.status === 'pending'
  const isCreated = item.status === 'created'
  const isProcessing = !isDone && !isFailed && !isCancelled && !isQueued && !isPending && !isCreated

  const vals = STEP_KEYS.map(k => item[k])
  const done = vals.filter(s => s === 1).length
  const nextStep = isProcessing ? vals.findIndex(s => s !== 1) : -1
  const progress = (done / STEPS.length) * 100

  const handleCopySession = () => {
    if (item.session_id) {
      navigator.clipboard.writeText(item.session_id)
    }
  }

  const handleReprocess = async () => {
    if (!onReprocess || processing) return
    setProcessing(true)
    try { await onReprocess() } finally { setProcessing(false) }
  }

  const handleProcess = async () => {
    if (!onProcess || processing) return
    setProcessing(true)
    try { await onProcess() } finally { setProcessing(false) }
  }

  const startEdit = () => {
    setEditNotes(Array.isArray(item.notes) ? [...item.notes] : typeof item.notes === 'string' ? (() => { try { return JSON.parse(item.notes) } catch { return [] } })() : [])
    setEditLinks(Array.isArray(item.links) ? [...item.links] : typeof item.links === 'string' ? (() => { try { return JSON.parse(item.links) } catch { return [] } })() : [])
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
        body: JSON.stringify({ notes: editNotes })
      })
      await fetch(`/api/pending-companies/${item.id}/links`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ links: editLinks })
      })
      item.notes = editNotes
      item.links = editLinks
      setEditing(false)
    } finally { setSaving(false) }
  }

  const addEditNote = () => {
    if (!newNote.trim()) return
    setEditNotes(prev => [...prev, { type: 'text', content: newNote.trim() }])
    setNewNote('')
  }

  const removeEditNote = (idx) => {
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

  const removeEditLink = (idx) => {
    setEditLinks(prev => prev.filter((_, i) => i !== idx))
  }

  return (
    <div className={cn(
      "group/card w-full rounded-lg border bg-card p-1.5 min-w-0 overflow-hidden transition hover:shadow",
      isFailed && "border-red-500/30",
      isDone && "border-green-500/30"
    )}>
      {/* Row 1: Status dot + Company name */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <div className={cn(
          "w-2 h-2 rounded-full shrink-0",
          isDone ? "bg-green-500" : isFailed ? "bg-red-500" : isCancelled ? "bg-gray-500" : isProcessing ? "bg-blue-500 animate-pulse" : isQueued ? "bg-yellow-400" : isPending ? "bg-sky-400" : "bg-muted-foreground"
        )} />
        {item.source === 'reprocess' && <span className="text-3xs px-0.5 rounded bg-secondary text-secondary-foreground shrink-0">R</span>}
        <span className="text-2xs font-bold truncate min-w-0">{item.company_name || 'Processing...'}</span>
      </div>

      {/* Row 2: Step icons */}
      <div className="flex gap-1 mb-1 min-w-0">
        {STEPS.map((step, i) => {
          const d = vals[i] === 1
          const isActive = i === nextStep && !d
          return (
            <div key={i} className="flex-1 min-w-0 flex justify-center">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn(
                    "w-4 h-4 rounded-full border shrink-0 flex items-center justify-center",
                    d ? "bg-green-500 border-green-500 text-white" :
                    isActive ? "bg-primary border-primary text-primary-foreground animate-pulse" :
                    "bg-background border-border text-muted-foreground"
                  )}>
                    {d ? <Check className="w-2 h-2" /> : step.icon}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-2xs px-2 py-1">
                  {d ? `${step.label} — done` : isActive ? `${step.label} — in progress...` : step.label}
                </TooltipContent>
              </Tooltip>
            </div>
          )
        })}
      </div>

      {/* Row 3: Progress */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <span className="text-2xs font-semibold text-muted-foreground shrink-0">{done}/{STEPS.length}</span>
        <Progress value={progress} className="h-0.5 flex-1 min-w-0" />
      </div>

      {/* Row 3.5: Minimized notes & links OR edit form */}
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
          {/* Notes */}
          <div className="space-y-0.5">
            {editNotes.map((n, i) => (
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
          {/* Links */}
          <div className="space-y-0.5">
            {editLinks.map((l, i) => (
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
      ) : (Array.isArray(item.notes) && item.notes.length > 0) || (Array.isArray(item.links) && item.links.length > 0) ? (
        <div className="mb-1 min-w-0 space-y-px">
          {Array.isArray(item.notes) && item.notes.length > 0 && (
            <div className="flex items-center gap-1 min-w-0">
              <Note className="w-2 h-2 text-muted-foreground shrink-0" />
              <div className="text-2xs text-muted-foreground truncate min-w-0 leading-tight">
                {item.notes.length} note{item.notes.length !== 1 ? 's' : ''}: {item.notes.slice(0, 2).map(n => (n.content || '').slice(0, 25)).join('; ')}{item.notes.length > 2 ? '...' : ''}
              </div>
            </div>
          )}
          {Array.isArray(item.links) && item.links.length > 0 && (
            <div className="flex items-center gap-1 min-w-0">
              <Link className="w-2 h-2 text-primary shrink-0" />
              <div className="text-2xs text-muted-foreground truncate min-w-0 leading-tight">
                {item.links.length} link{item.links.length !== 1 ? 's' : ''}: {item.links.slice(0, 2).map(l => l.title || l.url?.slice(0, 25) || '').join(', ')}{item.links.length > 2 ? '...' : ''}
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

      {/* Row 4: Status + actions */}
      <div className="flex items-center gap-1 min-w-0">
        {item.input_text && item.input_type === 'url' && (
          <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0" onClick={(e) => { e.stopPropagation(); window.open(item.input_text, '_blank') }} title="Open URL">
            <LinkSimple className="w-1.5 h-1.5 text-primary" />
          </Button>
        )}
        <span className="text-2xs truncate flex-1 min-w-0 text-muted-foreground">
          {isProcessing && <span className="text-blue-500">{statusKey}...</span>}
          {isPending && <span className="text-sky-500">pending</span>}
          {isCreated && <span className="text-gray-400">created</span>}
          {isCancelled && <span className="text-gray-500">cancelled</span>}
          {isFailed && <span className="text-red-500" title={item.error || 'Failed'}><Warning className="w-1.5 h-1.5 inline mr-0.5" />{item.error ? item.error.slice(0, 50) : 'Failed'}</span>}
          {isQueued && <span className="text-yellow-500">queued</span>}
          {isDone && <span className="text-green-500">processed</span>}
          {item.session_id ? (
            <button onClick={(e) => { e.stopPropagation(); handleCopySession() }} className="text-3xs text-muted-foreground hover:text-foreground font-mono ml-1" title={`Click to copy: ${item.session_id}`}>
              {item.session_id.slice(0, 6)}...
            </button>
          ) : !isDone && !isCancelled ? (
            <span className="text-3xs text-muted-foreground/50 font-mono ml-1">no_session_id</span>
          ) : null}
        </span>
        <CardActions
          status={item.status}
          size="sm"
          disabled={processing}
          error={item.error}
          onDelete={onDelete}
          onProcess={handleProcess}
          onCancel={isProcessing ? handleReprocess : (onPause || undefined)}
          onMoveToCreated={onMoveToCreated}
        />
      </div>
    </div>
  )
}
