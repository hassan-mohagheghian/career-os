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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { JobCard } from '@/shared/components/ProcessedCards'
import { MultiSelect } from '@/shared/components/MultiSelect'

export default function JobsPage({
  jobs, filteredJobs, jobsTotal, filteredJobsCount,
  sortBy, setSortBy, sortDir, setSortDir,
  filterTech, setFilterTech, filterCities, setFilterCities, filterCompanies, setFilterCompanies,
  filterMatches, setFilterMatches, filterWorkTypes, setFilterWorkTypes,
  filterEmploymentTypes, setFilterEmploymentTypes, filterResponseStatus, setFilterResponseStatus,
  filterApplied, setFilterApplied, filterScores, setFilterScores, allCities, allCompanies, activeFilterCount,
  loadingMore, jobsScrollRef, jobsSentinelRef,
  openWorkflow,
  rescoreJob, deleteJob, requeueJob, openDrawer, refreshJobs, clearFilters, loadMoreJobs, onOpenCompany
}) {
  return (
    <div className="flex gap-2 h-[calc(100vh-80px)]">
      {/* Jobs column */}
      <div className="w-full flex flex-col rounded-lg border overflow-hidden bg-card">
        <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-green-500/10 to-green-500/5 border-b border-green-500/20">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="font-bold text-xs text-green-500">Jobs</span>
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
