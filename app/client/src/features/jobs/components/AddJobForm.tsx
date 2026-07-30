import { useState } from 'react'
import { Plus, X, Warning, LinkSimple, Note } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'

interface LinkItem {
  url: string
  title: string
}

interface NoteItem {
  title: string
  content: string
}

interface AddJobFormProps {
  onSubmit: (data: { job_post_url: string; job_title: string; links: LinkItem[]; notes: NoteItem[]; queue: boolean }) => void
  onCancel: () => void
  submitting?: boolean
  error?: string
}

export default function AddJobForm({ onSubmit, onCancel, submitting, error }: AddJobFormProps) {
  const [urlInput, setUrlInput] = useState('')
  const [titleInput, setTitleInput] = useState('')
  const [links, setLinks] = useState<LinkItem[]>([])
  const [notes, setNotes] = useState<NoteItem[]>([])

  const [newLinkTitle, setNewLinkTitle] = useState('')
  const [newLinkUrl, setNewLinkUrl] = useState('')
  const [showLinkInput, setShowLinkInput] = useState(false)

  const [newNoteTitle, setNewNoteTitle] = useState('')
  const [newNoteContent, setNewNoteContent] = useState('')
  const [showNoteInput, setShowNoteInput] = useState(false)

  const urlValid = urlInput.trim().startsWith('http')

  const handleAddLink = () => {
    if (!newLinkUrl.trim()) return
    let url = newLinkUrl.trim()
    if (!url.startsWith('http')) url = 'https://' + url
    setLinks(prev => [...prev, { url, title: newLinkTitle.trim() }])
    setNewLinkUrl('')
    setNewLinkTitle('')
    setShowLinkInput(false)
  }

  const handleRemoveLink = (index: number) => {
    setLinks(prev => prev.filter((_, i) => i !== index))
  }

  const handleAddNote = () => {
    if (!newNoteContent.trim()) return
    setNotes(prev => [...prev, { title: newNoteTitle.trim(), content: newNoteContent.trim() }])
    setNewNoteContent('')
    setNewNoteTitle('')
    setShowNoteInput(false)
  }

  const handleRemoveNote = (index: number) => {
    setNotes(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = (queue: boolean) => {
    if (!urlValid) return
    onSubmit({
      job_post_url: urlInput.trim(),
      job_title: titleInput.trim(),
      links,
      notes,
      queue,
    })
  }

  const canSubmit = !!urlInput.trim() && urlValid

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4">
        {/* Job Post URL */}
        <div>
          <label className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
            <span>Job Post URL</span>
            <span className="text-destructive">*</span>
          </label>
          <Input
            type="url"
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            placeholder="https://linkedin.com/jobs/view/..."
            className={cn(
              "w-full",
              urlInput && !urlValid && "border-destructive"
            )}
          />
          {urlInput && !urlValid && (
            <p className="text-xs text-destructive mt-1">URL must start with http:// or https://</p>
          )}
        </div>

        {/* Job Title */}
        <div>
          <label className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
            <span>Job Title</span>
            <span className="text-muted-foreground/60">(optional)</span>
          </label>
          <Input
            type="text"
            value={titleInput}
            onChange={e => setTitleInput(e.target.value)}
            placeholder="Senior Backend Engineer"
          />
        </div>

        <hr className="border-border" />

        {/* Additional Links */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <LinkSimple className="w-3.5 h-3.5" />
              <span>Additional Links</span>
            </div>
            {!showLinkInput && (
              <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={() => setShowLinkInput(true)}>
                <Plus className="w-3 h-3" /> Add Link
              </Button>
            )}
          </div>

          {links.length === 0 && !showLinkInput && (
            <p className="text-xs text-muted-foreground/60">No additional links</p>
          )}

          {links.length > 0 && (
            <div className="space-y-2 mb-3">
              {links.map((link, i) => (
                <div key={i} className="rounded border bg-muted/50 p-2 space-y-1">
                  {link.title && (
                    <p className="text-xs font-medium">{link.title}</p>
                  )}
                  <div className="flex items-start gap-1">
                    <LinkSimple className="w-3 h-3 text-primary shrink-0 mt-0.5" />
                    <a href={link.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline break-all flex-1 min-w-0">
                      {link.url}
                    </a>
                    <button onClick={() => handleRemoveLink(i)} className="shrink-0 text-muted-foreground hover:text-destructive transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {showLinkInput && (
            <div className="rounded border bg-muted/50 p-3 space-y-2">
              <div>
                <label className="text-xs text-muted-foreground mb-0.5 block">Title (optional)</label>
                <div className="flex items-center gap-1">
                  {['LinkedIn', 'Website', 'Careers', 'GitHub'].map(label => (
                    <button key={label} type="button"
                      onClick={() => setNewLinkTitle(newLinkTitle === label ? '' : label)}
                      className={cn("h-6 px-2 rounded text-xs border transition-colors",
                        newLinkTitle === label
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background text-muted-foreground border-border hover:bg-muted"
                      )}>{label}</button>
                  ))}
                  <Input
                    type="text"
                    value={newLinkTitle}
                    onChange={e => setNewLinkTitle(e.target.value)}
                    placeholder="Custom"
                    className="h-6 text-xs flex-1"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-0.5 block">URL *</label>
                <Input
                  type="url"
                  value={newLinkUrl}
                  onChange={e => setNewLinkUrl(e.target.value)}
                  placeholder="https://..."
                  className="h-7 text-xs"
                  onKeyDown={e => e.key === 'Enter' && handleAddLink()}
                />
              </div>
              <div className="flex justify-end gap-1">
                <Button size="sm" variant="ghost" className="h-6 text-xs"
                  onClick={() => { setShowLinkInput(false); setNewLinkUrl(''); setNewLinkTitle('') }}>
                  Cancel
                </Button>
                <Button size="sm" variant="default" className="h-6 text-xs"
                  disabled={!newLinkUrl.trim()} onClick={handleAddLink}>
                  Add
                </Button>
              </div>
            </div>
          )}
        </div>

        <hr className="border-border" />

        {/* Notes */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Note className="w-3.5 h-3.5" />
              <span>Notes</span>
            </div>
            {!showNoteInput && (
              <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={() => setShowNoteInput(true)}>
                <Plus className="w-3 h-3" /> Add Note
              </Button>
            )}
          </div>

          {notes.length === 0 && !showNoteInput && (
            <p className="text-xs text-muted-foreground/60">No notes</p>
          )}

          {notes.length > 0 && (
            <div className="space-y-2 mb-3">
              {notes.map((note, i) => (
                <div key={i} className="rounded border bg-muted/50 p-2 space-y-1">
                  <div className="flex items-start justify-between gap-1">
                    <div className="flex-1 min-w-0">
                      {note.title && (
                        <p className="text-xs font-medium">{note.title}</p>
                      )}
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap">{note.content}</p>
                    </div>
                    <button onClick={() => handleRemoveNote(i)} className="shrink-0 text-muted-foreground hover:text-destructive transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {showNoteInput && (
            <div className="rounded border bg-muted/50 p-3 space-y-2">
              <div>
                <label className="text-xs text-muted-foreground mb-0.5 block">Title (optional)</label>
                <div className="flex items-center gap-1">
                  {['Requirements', 'Benefits', 'Salary', 'Description'].map(label => (
                    <button key={label} type="button"
                      onClick={() => setNewNoteTitle(newNoteTitle === label ? '' : label)}
                      className={cn("h-6 px-2 rounded text-xs border transition-colors",
                        newNoteTitle === label
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background text-muted-foreground border-border hover:bg-muted"
                      )}>{label}</button>
                  ))}
                  <Input
                    type="text"
                    value={newNoteTitle}
                    onChange={e => setNewNoteTitle(e.target.value)}
                    placeholder="Custom"
                    className="h-6 text-xs flex-1"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-0.5 block">Content *</label>
                <Textarea
                  value={newNoteContent}
                  onChange={e => setNewNoteContent(e.target.value)}
                  placeholder="Raw copied text..."
                  className="min-h-[60px] text-xs resize-none"
                  onKeyDown={e => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      e.preventDefault()
                      handleAddNote()
                    }
                  }}
                />
              </div>
              <div className="flex justify-end gap-1">
                <Button size="sm" variant="ghost" className="h-6 text-xs"
                  onClick={() => { setShowNoteInput(false); setNewNoteContent(''); setNewNoteTitle('') }}>
                  Cancel
                </Button>
                <Button size="sm" variant="default" className="h-6 text-xs"
                  disabled={!newNoteContent.trim()} onClick={handleAddNote}>
                  Add
                </Button>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="flex items-center gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
            <Warning className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}
      </div>

      <div className="flex items-center justify-end gap-2 pt-4 border-t mt-4 shrink-0">
        <Button variant="outline" size="sm" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
        <Button variant="default" size="sm" disabled={!canSubmit || submitting} onClick={() => handleSubmit(false)}>
          {submitting ? 'Creating...' : 'Create Job'}
        </Button>
        <Button variant="secondary" size="sm" disabled={!canSubmit || submitting} onClick={() => handleSubmit(true)}>
          {submitting ? 'Creating...' : 'Create & Queue'}
        </Button>
      </div>
    </div>
  )
}
