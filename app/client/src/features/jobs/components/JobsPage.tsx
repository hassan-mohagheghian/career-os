import { useState } from 'react'
import {
  Gear, X, CheckCircle, Clock, Stack, Warning, Buildings,
  ArrowsClockwise, Target, HouseSimple, Briefcase, MapPin,
  PaperPlaneRight
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Input } from '@/shared/ui/input'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import ProcessingItem from '@/shared/components/ProcessingItem'
import { JobCard } from '@/shared/components/ProcessedCards'
import { MultiSelect } from '@/shared/components/MultiSelect'
import NotesLinksInput from '@/shared/components/NotesLinksInput'
import JobPendingCard from './JobPendingCard'
import JobProcessingCard from './JobProcessingCard'
import JobFailedCard from './JobFailedCard'

export default function JobsPage({
  pending, jobs, filteredJobs, jobsTotal, filteredJobsCount,
  urlInput, setUrlInput, urlError, setUrlError, submitting, processImmediately, setProcessImmediately,
  sortBy, setSortBy, sortDir, setSortDir,
  filterTech, setFilterTech, filterCities, setFilterCities, filterCompanies, setFilterCompanies,
  filterMatches, setFilterMatches, filterWorkTypes, setFilterWorkTypes,
  filterEmploymentTypes, setFilterEmploymentTypes, filterResponseStatus, setFilterResponseStatus,
  filterApplied, setFilterApplied, filterScores, setFilterScores, allCities, allCompanies, activeFilterCount,
  collapsedSections, setCollapsedSections,
  loadingMore, jobsScrollRef, jobsSentinelRef,
  submitUrl, deletePending, processPending, resetPending, pausePending, openWorkflow,
  rescoreJob, deleteJob, requeueJob, openDrawer, refreshJobs, clearFilters, loadMoreJobs, onOpenCompany
}) {
  const createdCount = pending.filter(p => p.status === 'created').length
  const queuedCount = pending.filter(p => p.status === 'queued' || p.status === 'waiting').length
  const processingCount = pending.filter(p => ['starting','fetching','analyzing','generating','finalizing'].includes(p.status)).length
  const failedCount = pending.filter(p => p.status === 'failed' || p.status === 'cancelled').length
  const stackedTotal = createdCount + queuedCount + processingCount + failedCount

  const [dragId, setDragId] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)
  const [jobNotes, setJobNotes] = useState<Array<{ type: string; content: string }>>([])
  const [jobLinks, setJobLinks] = useState<Array<{ url: string; title: string }>>([])

  const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
  const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
  const handleDragLeave = () => { setDragOverCol(null) }
  const handleDrop = (e, colId) => {
    e.preventDefault(); setDragOverCol(null)
    if (!dragId) return
    if (colId === 'created') resetPending(dragId)
    else if (colId === 'queued') processPending(dragId)
    else if (colId === 'processing') processPending(dragId)
    setDragId(null)
  }

  return (
    <div className="flex gap-2 h-[calc(100vh-80px)]">
      {/* Processing Jobs column */}
      <div className="w-1/4 flex flex-col rounded-lg border overflow-hidden bg-card">
        <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-primary/20">
          <Gear className="w-4 h-4 text-primary" />
          <span className="font-bold text-xs text-primary">Processing Jobs</span>
          <Badge variant="default" className="ml-auto text-2xs h-4">{stackedTotal}</Badge>
        </div>
        <div className="flex flex-col flex-1 min-h-0 p-2">
          <NotesLinksInput
            urlInput={urlInput}
            setUrlInput={setUrlInput}
            notes={jobNotes}
            links={jobLinks}
            onAddNote={(note) => setJobNotes(prev => [...prev, note])}
            onRemoveNote={(i) => setJobNotes(prev => prev.filter((_, idx) => idx !== i))}
            onAddLink={(link) => setJobLinks(prev => [...prev, link])}
            onRemoveLink={(i) => setJobLinks(prev => prev.filter((_, idx) => idx !== i))}
            onSubmit={() => submitUrl(jobNotes, jobLinks)}
            submitting={submitting}
            processImmediately={processImmediately}
            onToggleProcess={() => setProcessImmediately(v => !v)}
            error={urlError}
          />
          <div className="flex flex-col flex-1 min-h-0 gap-1">
            {[
              { id: 'created', count: createdCount, label: 'Pending', icon: <Clock className="w-3 h-3" />, color: 'gray', iconClass: 'text-gray-500', bgClass: 'bg-gradient-to-r from-gray-500/10 to-gray-500/5', borderClass: 'border-b border-gray-500/20', textClass: 'text-gray-600 dark:text-gray-400' },
              { id: 'queued', count: queuedCount, label: 'Queued', icon: <Stack className="w-3 h-3" />, color: 'yellow', iconClass: 'text-yellow-500', bgClass: 'bg-gradient-to-r from-yellow-500/10 to-yellow-500/5', borderClass: 'border-b border-yellow-500/20', textClass: 'text-yellow-600 dark:text-yellow-500' },
              { id: 'processing', count: processingCount, label: 'Processing', icon: <Gear className="w-3 h-3" />, color: 'blue', iconClass: 'text-blue-500', bgClass: 'bg-gradient-to-r from-blue-500/10 to-blue-500/5', borderClass: 'border-b border-blue-500/20', textClass: 'text-blue-600 dark:text-blue-500' },
              { id: 'failed', count: failedCount, label: 'Failed/Cancelled', icon: <X className="w-3 h-3" />, color: 'red', iconClass: 'text-red-500', bgClass: 'bg-gradient-to-r from-red-500/10 to-red-500/5', borderClass: 'border-b border-red-500/20', textClass: 'text-red-600 dark:text-red-500' },
            ].map(s => {
              const isEmpty = s.count === 0
              const isOpen = isEmpty ? false : !collapsedSections[s.id]
              return (
                <div key={s.id} className={cn("flex flex-col rounded-lg border min-w-0 max-w-full overflow-hidden", isOpen ? "flex-1 min-h-0" : "")}>
                  <div onClick={() => !isEmpty && setCollapsedSections(prev => ({ ...prev, [s.id]: !prev[s.id] }))}
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
                          <JobPendingCard key={p.num} item={p} onProcess={() => processPending(p.num)} onDelete={() => deletePending(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'queued' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'queued')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'queued')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'queued' || p.status === 'waiting').map(p =>
                          <ProcessingItem key={p.num} item={p} onProcess={() => processPending(p.num)} onDelete={() => deletePending(p.num)} onReset={() => resetPending(p.num)} onDragStart={e => handleDragStart(e, p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'processing' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0"
                      onDragOver={e => handleDragOver(e, 'processing')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'processing')}>
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => ['starting','fetching','analyzing','generating','finalizing'].includes(p.status)).map(p =>
                          <JobProcessingCard key={p.num} item={p} onDragStart={e => handleDragStart(e, p.num)}
                            onCancel={() => pausePending(p.num)} onDelete={() => deletePending(p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                  {isOpen && s.id === 'failed' && (
                    <ScrollArea className="flex-1 min-h-0 min-w-0">
                      <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                        {pending.filter(p => p.status === 'failed' || p.status === 'cancelled').map(p =>
                          <JobFailedCard key={p.num} item={p} onDelete={() => deletePending(p.num)} onProcess={() => processPending(p.num)} onReset={() => resetPending(p.num)} onViewWorkflow={openWorkflow} />)}
                      </div>
                    </ScrollArea>
                  )}
                </div>
              )
            })}
          </div>
          {stackedTotal === 0 && <div className="text-center py-2 text-2xs text-muted-foreground shrink-0">All jobs processed</div>}
        </div>
      </div>

      {/* Processed Jobs column */}
      <div className="w-3/4 flex flex-col rounded-lg border overflow-hidden bg-card">
        <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-green-500/10 to-green-500/5 border-b border-green-500/20">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="font-bold text-xs text-green-500">Processed Jobs</span>
          <Badge variant="secondary" className="text-2xs h-4 bg-green-500/15 text-green-500">{filteredJobsCount}/{jobsTotal}</Badge>
          <div className="flex items-center gap-0.5 ml-auto">
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => refreshJobs()} title="Refresh"><ArrowsClockwise className="w-3 h-3 text-green-500" /></Button>
          </div>
        </div>
        <div ref={jobsScrollRef} className="flex-1 overflow-y-auto">
          <div className="sticky top-0 z-10 bg-card p-2 pb-0">
            <div className="flex items-center gap-1 mb-2">
              <div className="relative flex-1">
                <Input value={filterTech} onChange={e => setFilterTech(e.target.value)}
                  placeholder="Search by role, company, stack, or notes..."
                  className={cn("w-full h-7 text-xs", filterTech && "border-green-500 ring-1 ring-green-500/20")} />
                {filterTech && <button onClick={() => setFilterTech('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-2xs text-muted-foreground">✕</button>}
              </div>
              {activeFilterCount > 0 && <Button variant="ghost" size="sm" className="h-7 text-2xs text-green-500 hover:text-green-600 hover:bg-green-500/10" onClick={clearFilters}>Clear all</Button>}
            </div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-1">
                <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setSortDir('desc') }}>
                  <SelectTrigger className="h-7 w-auto text-2xs border-green-500/30"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Newest first</SelectItem>
                    <SelectItem value="overall_score">Overall Score</SelectItem>
                    <SelectItem value="fit_score">Fit Score</SelectItem>
                    <SelectItem value="success_score">Success Score</SelectItem>
                    <SelectItem value="posted_at">Posted date</SelectItem>
                    <SelectItem value="applicants">Applicants</SelectItem>
                    <SelectItem value="company">Company</SelectItem>
                    <SelectItem value="location">Location</SelectItem>
                    <SelectItem value="apply_time">Applied date</SelectItem>
                    <SelectItem value="response_time">Response date</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm" className="h-7 text-2xs border-green-500/30 text-green-500 hover:bg-green-500/10" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                  {sortDir === 'desc' ? '↓' : '↑'}
                </Button>
              </div>
              <div className="flex items-center gap-1 flex-wrap justify-end">
                <MultiSelect value={filterCities} onChange={setFilterCities} placeholder="City" icon={<MapPin className="w-3 h-3" />} options={allCities.map(c => ({ value: c, label: c }))} />
                <MultiSelect value={filterCompanies} onChange={setFilterCompanies} placeholder="Co" icon={<Buildings className="w-3 h-3" />} options={allCompanies.map(c => ({ value: c, label: c }))} />
                <MultiSelect value={filterMatches} onChange={setFilterMatches} placeholder="Match" icon={<Target className="w-3 h-3" />} options={[{ value: 'High', label: 'High' }, { value: 'Medium', label: 'Medium' }, { value: 'Low', label: 'Low' }]} />
                <MultiSelect value={filterWorkTypes} onChange={setFilterWorkTypes} placeholder="Work" icon={<HouseSimple className="w-3 h-3" />} options={[{ value: 'On-site', label: 'On-site' }, { value: 'Remote', label: 'Remote' }, { value: 'Hybrid', label: 'Hybrid' }]} />
                <MultiSelect value={filterEmploymentTypes} onChange={setFilterEmploymentTypes} placeholder="Emp" icon={<Briefcase className="w-3 h-3" />} options={[{ value: 'Full-time', label: 'Full-time' }, { value: 'Part-time', label: 'Part-time' }, { value: 'Contract', label: 'Contract' }, { value: 'Internship', label: 'Internship' }, { value: 'Temporary', label: 'Temporary' }]} />
                <MultiSelect value={filterResponseStatus} onChange={setFilterResponseStatus} placeholder="Status" icon={<CheckCircle className="w-3 h-3" />} options={[{ value: 'Interview', label: 'Interview' }, { value: 'Rejected', label: 'Rejected' }]} />
                <MultiSelect value={filterScores} onChange={setFilterScores} placeholder="Score" icon={<Target className="w-3 h-3" />} options={[{ value: 'A++', label: 'A++' }, { value: 'A+', label: 'A+' }, { value: 'A', label: 'A' }, { value: 'B', label: 'B' }, { value: 'C', label: 'C' }, { value: 'D', label: 'D' }, { value: 'E', label: 'E' }]} />
                <Button variant={filterApplied ? "default" : "outline"} size="sm" className={cn("h-7 text-2xs", filterApplied && "bg-green-500/20 text-green-500 border-green-500/30 hover:bg-green-500/30")} onClick={() => setFilterApplied(f => !f)}>
                  <PaperPlaneRight className="w-3 h-3 mr-0.5" />Applied
                </Button>
              </div>
            </div>
          </div>
          <div className="p-2">
            <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
              {filteredJobs.map((j, i) => <JobCard key={j.num} job={j} rank={i + 1} onClick={() => openDrawer(j.num)} onRescore={rescoreJob} onDelete={deleteJob} onRequeue={requeueJob} onViewWorkflow={openWorkflow} onOpenCompany={onOpenCompany} />)}
            </div>
            <div ref={jobsSentinelRef} className="h-1" />
            {loadingMore && <div className="text-center py-2 text-2xs text-muted-foreground">Loading more...</div>}
            {!loadingMore && filteredJobsCount >= jobsTotal && filteredJobsCount > 0 && <div className="text-center py-2 text-2xs text-muted-foreground opacity-50">All {jobsTotal} jobs loaded</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
