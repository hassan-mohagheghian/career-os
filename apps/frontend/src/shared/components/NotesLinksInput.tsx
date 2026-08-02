import { useState } from 'react'
import {
  Plus, X, CheckCircle, Warning, LinkSimple, Note, ArrowSquareUp,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'

interface NoteItem {
  type: 'text' | 'url'
  content: string
}

interface LinkItem {
  url: string
  title: string
}

interface NotesLinksInputProps {
  urlInput: string
  setUrlInput: (val: string) => void
  notes: NoteItem[]
  links: LinkItem[]
  onAddNote: (note: NoteItem) => void
  onRemoveNote: (index: number) => void
  onAddLink: (link: LinkItem) => void
  onRemoveLink: (index: number) => void
  onSubmit: () => void
  submitting: boolean
  processImmediately: boolean
  onToggleProcess: () => void
  error?: string
  placeholder?: string
  disabled?: boolean
  editingId?: number | null
  onCancelEdit?: () => void
}

function NoteItemDisplay({ note, onRemove }: { note: NoteItem; onRemove?: () => void }) {
  const isUrl = note.type === 'url' || (note.content || '').startsWith('http')
  return (
    <div className="flex items-start gap-1 group/note rounded border bg-muted/50 px-2 py-1 text-2xs">
      <span className="shrink-0 mt-0.5">
        {isUrl ? <LinkSimple className="w-2.5 h-2.5 text-primary" /> : <Note className="w-2.5 h-2.5 text-muted-foreground" />}
      </span>
      <span className="flex-1 min-w-0 break-all">
        {isUrl ? (
          <a href={note.content} target="_blank" rel="noreferrer" className="text-primary hover:underline">{note.content}</a>
        ) : note.content}
      </span>
      {onRemove && (
        <button onClick={onRemove} className="shrink-0 opacity-0 group-hover/note:opacity-100 transition text-muted-foreground hover:text-destructive">
          <X className="w-2.5 h-2.5" />
        </button>
      )}
    </div>
  )
}

function LinkItemDisplay({ link, onRemove }: { link: LinkItem; onRemove?: () => void }) {
  return (
    <div className="flex items-start gap-1 group/link rounded border bg-muted/50 px-2 py-1 text-2xs">
      <LinkSimple className="w-2.5 h-2.5 text-primary shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <a href={link.url} target="_blank" rel="noreferrer" className="text-primary hover:underline break-all">{link.url}</a>
        {link.title && <div className="text-muted-foreground truncate">{link.title}</div>}
      </div>
      {onRemove && (
        <button onClick={onRemove} className="shrink-0 opacity-0 group-hover/link:opacity-100 transition text-muted-foreground hover:text-destructive">
          <X className="w-2.5 h-2.5" />
        </button>
      )}
    </div>
  )
}

export default function NotesLinksInput({
  urlInput, setUrlInput, notes, links, onAddNote, onRemoveNote, onAddLink, onRemoveLink,
  onSubmit, submitting, processImmediately, onToggleProcess,
  error, placeholder = 'Add a note...', disabled, editingId, onCancelEdit,
}: NotesLinksInputProps) {
  const [noteInput, setNoteInput] = useState('')
  const [linkUrl, setLinkUrl] = useState('')
  const [linkTitle, setLinkTitle] = useState('')
  const [showLinkInput, setShowLinkInput] = useState(false)

  const handleAddNote = () => {
    if (!noteInput.trim()) return
    onAddNote({ type: 'text', content: noteInput.trim() })
    setNoteInput('')
  }

  const handleAddLink = () => {
    if (!linkUrl.trim()) return
    let url = linkUrl.trim()
    if (!url.startsWith('http')) url = 'https://' + url
    onAddLink({ url, title: linkTitle.trim() })
    setLinkUrl('')
    setLinkTitle('')
    setShowLinkInput(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAddNote()
    }
  }

  const canSubmit = !!urlInput.trim()

  return (
    <div className="rounded border p-1.5 shrink-0 mb-1 bg-muted min-w-0">
      {editingId && (
        <div className="flex items-center gap-1 mb-1 text-2xs text-primary">
          <Plus className="w-2.5 h-2.5" />
          <span>Adding to pending #{editingId}</span>
          <button onClick={onCancelEdit} className="ml-auto text-muted-foreground hover:text-foreground"><X className="w-2.5 h-2.5" /></button>
        </div>
      )}

      {/* Job URL (required) */}
      <div className="mb-1">
        <div className="flex items-center gap-1 text-2xs text-muted-foreground mb-0.5">
          <ArrowSquareUp className="w-2.5 h-2.5" />
          <span>Job Link</span>
          <span className="text-destructive">*</span>
        </div>
        <Input
          type="url"
          value={urlInput}
          onChange={e => setUrlInput(e.target.value)}
          placeholder="https://linkedin.com/jobs/view/..."
          className={cn(
            "w-full h-7 rounded border text-2xs px-2 bg-background",
            urlInput && !urlInput.startsWith('http') && "border-destructive"
          )}
        />
        {urlInput && !urlInput.startsWith('http') && (
          <div className="text-2xs text-destructive mt-0.5 px-0.5">URL must start with http:// or https://</div>
        )}
      </div>

      {/* Notes section (optional) */}
      <div className="mb-1 border-t pt-1 mt-1">
        <div className="flex items-center gap-1 text-2xs text-muted-foreground mb-0.5">
          <Note className="w-2.5 h-2.5" />
          <span>Notes</span>
          <span className="text-muted-foreground/60">(optional)</span>
        </div>
        {notes.length > 0 && (
          <div className="space-y-0.5 mb-1 max-h-16 overflow-y-auto">
            {notes.map((note, i) => (
              <NoteItemDisplay key={i} note={note} onRemove={() => onRemoveNote(i)} />
            ))}
          </div>
        )}
        <div className="flex gap-1">
          <Textarea value={noteInput} onChange={e => setNoteInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste job description text..."
            className="w-full h-8 rounded border text-2xs min-w-0 resize-none flex-1" />
          <Button onClick={handleAddNote} disabled={!noteInput.trim()} size="sm" variant="outline" className="h-8 px-2 shrink-0">
            <Plus className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {/* Links section */}
      <div className="border-t pt-1 mt-1">
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-1 text-2xs text-muted-foreground">
            <LinkSimple className="w-2.5 h-2.5" />
            <span>Links</span>
            <span className="text-muted-foreground/60">(optional)</span>
          </div>
          {!showLinkInput && (
            <button onClick={() => setShowLinkInput(true)} className="text-2xs text-primary hover:underline flex items-center gap-0.5">
              <Plus className="w-2 h-2" /> Add
            </button>
          )}
        </div>
        {links.length > 0 && (
          <div className="space-y-0.5 mb-1 max-h-16 overflow-y-auto">
            {links.map((link, i) => (
              <LinkItemDisplay key={i} link={link} onRemove={() => onRemoveLink(i)} />
            ))}
          </div>
        )}
        {showLinkInput && (
          <div className="space-y-0.5">
            <input type="url" value={linkUrl} onChange={e => setLinkUrl(e.target.value)}
              placeholder="URL (https://...)"
              className="w-full h-6 rounded border text-2xs px-1.5 bg-background"
              onKeyDown={e => e.key === 'Enter' && handleAddLink()} />
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
              <input type="text" value={linkTitle} onChange={e => setLinkTitle(e.target.value)}
                placeholder="Custom title"
                className="flex-1 h-5 rounded border text-2xs px-1.5 bg-background" />
            </div>
            <div className="flex justify-end gap-1">
              <Button onClick={handleAddLink} disabled={!linkUrl.trim()} size="sm" variant="ghost" className="h-5 px-1.5 text-2xs">
                <CheckCircle className="w-2 h-2 mr-0.5" /> Add
              </Button>
              <Button onClick={() => { setShowLinkInput(false); setLinkUrl(''); setLinkTitle('') }} size="sm" variant="ghost" className="h-5 px-1 text-2xs">
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      {error && <div className="text-2xs mt-1 px-0.5 flex items-center gap-1 text-destructive"><Warning className="w-2.5 h-2.5" /> {error}</div>}

      <div className="flex items-center gap-1 mt-1.5">
        <Button onClick={onSubmit} disabled={submitting || disabled || !canSubmit} size="sm" className="flex-1 h-6 text-2xs">
          {submitting ? '...' : editingId ? 'Add & Process' : processImmediately ? 'Add & Process' : 'Add'}
        </Button>
        {!editingId && (
          <button
            onClick={onToggleProcess}
            className={cn(
              "shrink-0 h-6 px-1.5 rounded text-2xs font-medium border transition-colors",
              processImmediately
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background text-muted-foreground border-border hover:bg-muted"
            )}
          >
            {processImmediately ? 'Auto' : 'Queue'}
          </button>
        )}
      </div>
    </div>
  )
}

export { NoteItemDisplay, LinkItemDisplay }
