import { useState, useMemo, useEffect } from 'react'
import {
  Buildings, X, CheckCircle, MagnifyingGlass, Note, LinkSimple, ArrowSquareOut,
  Clock, Stack, Gear
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Input } from '@/shared/ui/input'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Textarea } from '@/shared/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import CompanyCard from './CompanyCard'
import CompanyDrawer from './CompanyDrawer'
import ProcessingItem from '@/shared/components/ProcessingItem'
import ConfirmDialog from '@/shared/components/ConfirmDialog'

const API = '/api'

function parseNotes(notes) {
  if (!notes) return []
  if (Array.isArray(notes)) return notes
  if (typeof notes === 'string') {
    try { return JSON.parse(notes) } catch { return [] }
  }
  return []
}

function NoteItem({ note, onRemove }) {
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

function LinkItem({ link, onRemove }) {
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

export default function CompaniesPage({ companies, deepLinkId, onClearDeepLink, onRefresh, onOpenJob, onNavigateToJob, onOpenCompany, pending = [], deletePending, processPending, resetPending, moveToCreated, pausePending, openWorkflow, collapsedSections, setCollapsedSections }) {
  const [noteInput, setNoteInput] = useState('')
  const [notes, setNotes] = useState([])
  const [links, setLinks] = useState([])
  const [linkUrl, setLinkUrl] = useState('')
  const [linkTitle, setLinkTitle] = useState('')
  const [showLinkInput, setShowLinkInput] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmDialog, setConfirmDialog] = useState(null)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [filterIndustry, setFilterIndustry] = useState('')
  const [_collapsedSections, _setCollapsedSections] = useState<Record<string, boolean>>({})
  const cs = collapsedSections ?? _collapsedSections
  const setCs = setCollapsedSections ?? _setCollapsedSections

  const createdCount = pending.filter(p => p.status === 'created').length
  const pendingCount = pending.filter(p => p.status === 'pending').length
  const queuedCount = pending.filter(p => p.status === 'queued').length
  const processingCount = pending.filter(p => p.status === 'processing').length
  const failedCount = pending.filter(p => p.status === 'failed' || p.status === 'cancelled').length
  const stackedTotal = createdCount + pendingCount + queuedCount + processingCount + failedCount

  const [dragId, setDragId] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
  const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
  const handleDragLeave = () => { setDragOverCol(null) }
  const handleDrop = (e, colId) => {
    e.preventDefault(); setDragOverCol(null)
    if (!dragId) return
    if (colId === 'created') resetPending?.(dragId)
    else if (colId === 'pending') processPending?.(dragId)
    else if (colId === 'queued') processPending?.(dragId)
    else if (colId === 'processing') processPending?.(dragId)
    setDragId(null)
  }

  useEffect(() => {
    if (deepLinkId && companies.length > 0) {
      onOpenCompany?.(deepLinkId)
      onClearDeepLink?.()
    }
  }, [deepLinkId, companies])

  useEffect(() => {
    const handleOpenCompany = (e) => {
      const id = e.detail
      if (id) onOpenCompany?.(id)
    }
    window.addEventListener('openCompany', handleOpenCompany)
    return () => window.removeEventListener('openCompany', handleOpenCompany)
  }, [companies])

  const allIndustries = useMemo(() => {
    const set = new Set(companies.map(c => c.industry).filter(Boolean))
    return [...set].sort()
  }, [companies])

  const PRIORITY_RANK = { 'A++': 6, 'A+': 5, 'A': 4, 'B': 3, 'C': 2 }

  const filteredCompanies = useMemo(() => {
    let r = [...companies]
    if (search) {
      const q = search.toLowerCase()
      r = r.filter(c =>
        (c.name || '').toLowerCase().includes(q) ||
        (c.industry || '').toLowerCase().includes(q) ||
        (c.city || '').toLowerCase().includes(q) ||
        (c.country || '').toLowerCase().includes(q) ||
        (c.description || '').toLowerCase().includes(q)
      )
    }
    if (filterIndustry) {
      r = r.filter(c => c.industry === filterIndustry)
    }
    r.sort((a, b) => {
      let aVal, bVal
      if (sortBy === 'name') {
        aVal = (a.name || '').toLowerCase(); bVal = (b.name || '').toLowerCase()
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      if (sortBy === 'priority') {
        aVal = PRIORITY_RANK[a.scores?.priority] || 0; bVal = PRIORITY_RANK[b.scores?.priority] || 0
      } else if (sortBy === 'visa_score') {
        aVal = a.scores?.visa_score || 0; bVal = b.scores?.visa_score || 0
      } else if (sortBy === 'tech_match') {
        aVal = a.scores?.tech_match || 0; bVal = b.scores?.tech_match || 0
      } else if (sortBy === 'career_score') {
        aVal = a.scores?.career_score || 0; bVal = b.scores?.career_score || 0
      } else {
        aVal = a.created_at ? new Date(a.created_at).getTime() : 0
        bVal = b.created_at ? new Date(b.created_at).getTime() : 0
      }
      return sortDir === 'desc' ? bVal - aVal : aVal - bVal
    })
    return r
  }, [companies, search, sortBy, sortDir, filterIndustry])

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setConfirmDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  const addNote = () => {
    if (!noteInput.trim()) return
    const type = noteInput.trim().startsWith('http') ? 'url' : 'text'
    setNotes(prev => [...prev, { type, content: noteInput.trim() }])
    setNoteInput('')
    setError('')
  }

  const removeNote = (idx) => {
    setNotes(prev => prev.filter((_, i) => i !== idx))
  }

  const addLink = () => {
    if (!linkUrl.trim()) return
    let url = linkUrl.trim()
    if (!url.startsWith('http')) url = 'https://' + url
    setLinks(prev => [...prev, { url, title: linkTitle.trim() }])
    setLinkUrl('')
    setLinkTitle('')
    setError('')
  }

  const removeLink = (idx) => {
    setLinks(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = async () => {
    if (notes.length === 0 && !noteInput.trim() && links.length === 0) return
    setError('')
    let allNotes = [...notes]
    if (noteInput.trim()) {
      const type = noteInput.trim().startsWith('http') ? 'url' : 'text'
      allNotes = [...allNotes, { type, content: noteInput.trim() }]
    }
    if (allNotes.length === 0 && links.length === 0) return
    setSubmitting(true)
    try {
      const res = await fetch(`${API}/pending-companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: allNotes, links, source: 'web' })
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Failed to add')
        setSubmitting(false)
        return
      }
      setNotes([])
      setLinks([])
      setNoteInput('')
      setLinkUrl('')
      setLinkTitle('')
      setShowLinkInput(false)
      setError('')
      onRefresh?.()
    } catch (e) {
      setError('Failed to add company')
    } finally {
      setSubmitting(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      addNote()
    }
  }

  const deleteCompany = async (id) => {
    const ok = await showConfirm('Delete Company', 'Permanently delete this company and all its intelligence data?', 'Delete')
    if (!ok) return
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    onRefresh?.()
  }

  const reprocessCompany = async (id) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    onRefresh?.()
  }

  const openCompany = async (id) => {
    onOpenCompany?.(id)
  }

  return (
    <div className="flex gap-2 h-[calc(100vh-80px)]">
      {/* Processing Companies column */}
      <div className="w-1/4 flex flex-col rounded-lg border overflow-hidden bg-card">
        <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-primary/20">
          <Buildings className="w-4 h-4 text-primary" />
          <span className="font-bold text-xs text-primary">Processing Companies</span>
          <Badge variant="default" className="ml-auto text-2xs h-4">{stackedTotal}</Badge>
        </div>
        <div className="flex flex-col flex-1 min-h-0 p-2">
          {/* Add Company form */}
          <div className="rounded border p-1.5 shrink-0 mb-1 bg-muted min-w-0">
            <div className="mb-1">
              <div className="flex items-center gap-1 text-2xs text-muted-foreground mb-0.5">
                <Note className="w-2.5 h-2.5" />
                <span>Add Company</span>
              </div>
              {notes.length > 0 && (
                <div className="space-y-0.5 mb-1 max-h-16 overflow-y-auto">
                  {notes.map((note, i) => (
                    <NoteItem key={i} note={note} onRemove={() => removeNote(i)} />
                  ))}
                </div>
              )}
              <div className="flex gap-1">
                <Textarea value={noteInput} onChange={e => { setNoteInput(e.target.value); setError('') }}
                  onKeyDown={handleKeyDown}
                  placeholder="Company name, description, observations..."
                  className="w-full h-8 rounded border text-2xs min-w-0 resize-none flex-1" />
                <Button onClick={addNote} disabled={!noteInput.trim()} size="sm" variant="outline" className="h-8 px-2 shrink-0">
                  +
                </Button>
              </div>
            </div>

            <div className="border-t pt-1 mt-1">
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-1 text-2xs text-muted-foreground">
                  <LinkSimple className="w-2.5 h-2.5" />
                  <span>Links</span>
                </div>
                {!showLinkInput && (
                  <button onClick={() => setShowLinkInput(true)} className="text-2xs text-primary hover:underline flex items-center gap-0.5">
                    + Add
                  </button>
                )}
              </div>
              {links.length > 0 && (
                <div className="space-y-0.5 mb-1 max-h-16 overflow-y-auto">
                  {links.map((link, i) => (
                    <LinkItem key={i} link={link} onRemove={() => removeLink(i)} />
                  ))}
                </div>
              )}
              {showLinkInput && (
                <div className="space-y-0.5">
                  <input type="url" value={linkUrl} onChange={e => setLinkUrl(e.target.value)}
                    placeholder="URL (https://...)"
                    className="w-full h-6 rounded border text-2xs px-1.5 bg-background"
                    onKeyDown={e => e.key === 'Enter' && addLink()} />
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
                    <Button onClick={addLink} disabled={!linkUrl.trim()} size="sm" variant="ghost" className="h-5 px-1.5 text-2xs">
                      <CheckCircle className="w-2 h-2 mr-0.5" /> Add
                    </Button>
                    <Button onClick={() => { setShowLinkInput(false); setLinkUrl(''); setLinkTitle('') }} size="sm" variant="ghost" className="h-5 px-1 text-2xs">
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {error && <div className="text-2xs mt-1 px-0.5 flex items-center gap-1 text-destructive">{error}</div>}

            <div className="flex items-center gap-1 mt-1.5">
              <Button onClick={handleSubmit} disabled={submitting || (notes.length === 0 && !noteInput.trim() && links.length === 0)} size="sm" className="flex-1 h-6 text-2xs">
                {submitting ? '...' : 'Add & Process'}
              </Button>
            </div>
          </div>

          {/* Status cards */}
          <div className="flex flex-col flex-1 min-h-0 gap-1">
            {[
              { id: 'created', count: createdCount, label: 'Created', icon: <Clock className="w-3 h-3" />, color: 'gray', iconClass: 'text-gray-500', bgClass: 'bg-gradient-to-r from-gray-500/10 to-gray-500/5', borderClass: 'border-b border-gray-500/20', textClass: 'text-gray-600 dark:text-gray-400' },
              { id: 'pending', count: pendingCount, label: 'Pending', icon: <Clock className="w-3 h-3" />, color: 'sky', iconClass: 'text-sky-500', bgClass: 'bg-gradient-to-r from-sky-500/10 to-sky-500/5', borderClass: 'border-b border-sky-500/20', textClass: 'text-sky-600 dark:text-sky-400' },
              { id: 'queued', count: queuedCount, label: 'Queued', icon: <Stack className="w-3 h-3" />, color: 'yellow', iconClass: 'text-yellow-500', bgClass: 'bg-gradient-to-r from-yellow-500/10 to-yellow-500/5', borderClass: 'border-b border-yellow-500/20', textClass: 'text-yellow-600 dark:text-yellow-500' },
              { id: 'processing', count: processingCount, label: 'Processing', icon: <Gear className="w-3 h-3" />, color: 'blue', iconClass: 'text-blue-500', bgClass: 'bg-gradient-to-r from-blue-500/10 to-blue-500/5', borderClass: 'border-b border-blue-500/20', textClass: 'text-blue-600 dark:text-blue-500' },
              { id: 'failed', count: failedCount, label: 'Failed/Cancelled', icon: <X className="w-3 h-3" />, color: 'red', iconClass: 'text-red-500', bgClass: 'bg-gradient-to-r from-red-500/10 to-red-500/5', borderClass: 'border-b border-red-500/20', textClass: 'text-red-600 dark:text-red-500' },
            ].map(s => {
              const isEmpty = s.count === 0
              const isOpen = isEmpty ? false : !cs[s.id]
              return (
                <div key={s.id} className={cn("flex flex-col rounded-lg border min-w-0 max-w-full overflow-hidden", isOpen ? "flex-1 min-h-0" : "")}>
                  <div onClick={() => !isEmpty && setCs(prev => ({ ...prev, [s.id]: !prev[s.id] }))}
                    className={cn("px-2 py-1 flex items-center gap-1 shrink-0 transition cursor-pointer select-none hover:bg-muted/50", s.bgClass, s.borderClass)}>
                    <span className={s.iconClass}>{s.icon}</span>
                    <span className={cn("font-bold text-2xs uppercase tracking-wider", s.textClass)}>{s.label}</span>
                    <Badge variant="secondary" className={cn("text-2xs h-4 ml-auto", isEmpty && "opacity-50")}>{s.count}</Badge>
                    {!isEmpty && <span className="text-2xs text-muted-foreground">{isOpen ? '▾' : '▸'}</span>}
                  </div>
                  {isOpen && s.id === 'created' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'created')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'created')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'created').map(p =>
                          <ProcessingItem key={p.num} item={p} onProcess={() => processPending?.(p.num)} onDelete={() => deletePending?.(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'pending' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'pending')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'pending')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'pending').map(p =>
                          <ProcessingItem key={p.num} item={p} onProcess={() => processPending?.(p.num)} onDelete={() => deletePending?.(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'queued' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'queued')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'queued')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'queued').map(p =>
                          <ProcessingItem key={p.num} item={p} onProcess={() => processPending?.(p.num)} onDelete={() => deletePending?.(p.num)} onMoveToCreated={() => resetPending?.(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'processing' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'processing')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'processing')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'processing').map(p =>
                          <ProcessingItem key={p.num} item={p} onDragStart={e => handleDragStart(e, p.num)}
                            onPause={() => pausePending?.(p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'failed' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0">
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'failed' || p.status === 'cancelled').map(p =>
                          <ProcessingItem key={p.num} item={p} onDelete={() => deletePending?.(p.num)} onProcess={() => processPending?.(p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Processed Companies column */}
      <div className="w-3/4 flex flex-col rounded-lg border overflow-hidden bg-card">
        <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-green-500/10 to-green-500/5 border-b border-green-500/20">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="font-bold text-xs text-green-500">Companies</span>
          <Badge variant="secondary" className="text-2xs h-4 bg-green-500/15 text-green-500">{filteredCompanies.length}/{companies.length}</Badge>
          <div className="flex items-center gap-0.5 ml-auto">
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onRefresh} title="Refresh">
              <ArrowSquareOut className="w-3 h-3 text-green-500" />
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {companies.length === 0 ? (
            <div className="text-center py-12">
              <Buildings className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
              <p className="text-sm font-semibold mb-1">No companies yet</p>
              <p className="text-xs text-muted-foreground">Add notes about a company (URLs, descriptions, anything) to get started.</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-1 mb-2 sticky top-0 z-10 bg-card pb-1">
                <div className="relative flex-1">
                  <MagnifyingGlass className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
                  <Input value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Search by name, industry, city..."
                    className="w-full h-7 text-xs pl-7" />
                  {search && <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-2xs text-muted-foreground">✕</button>}
                </div>
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="h-7 w-auto text-2xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Newest</SelectItem>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="visa_score">Visa Score</SelectItem>
                    <SelectItem value="tech_match">Tech Match</SelectItem>
                    <SelectItem value="career_score">Career Score</SelectItem>
                    <SelectItem value="priority">Priority</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm" className="h-7 text-2xs" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                  {sortDir === 'desc' ? '↓' : '↑'}
                </Button>
                {allIndustries.length > 0 && (
                  <Select value={filterIndustry} onValueChange={setFilterIndustry}>
                    <SelectTrigger className="h-7 w-auto text-2xs"><SelectValue placeholder="Industry" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Industries</SelectItem>
                      {allIndustries.map((ind: string) => (
                        <SelectItem key={ind} value={ind}>{ind}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {(search || filterIndustry) && (
                  <Button variant="ghost" size="sm" className="h-7 text-2xs text-green-500" onClick={() => { setSearch(''); setFilterIndustry('') }}>Clear</Button>
                )}
              </div>
              <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))' }}>
                {filteredCompanies.map(c => (
                  <CompanyCard key={c.id} company={c}
                    onClick={() => openCompany(c.id)}
                    onDelete={deleteCompany}
                    onReprocess={reprocessCompany} />
                ))}
              </div>
              {filteredCompanies.length === 0 && companies.length > 0 && (
                <div className="text-center py-6 text-xs text-muted-foreground">No companies match your search</div>
              )}
            </>
          )}
        </div>
      </div>

      <ConfirmDialog dialog={confirmDialog} onClose={() => setConfirmDialog(null)} />
    </div>
  )
}
