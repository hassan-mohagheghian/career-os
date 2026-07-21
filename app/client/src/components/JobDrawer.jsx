import {
  TrendUp, Repeat, Link, Lightning, ListChecks, Star, Gift, Shield,
  FileText, Spinner, PaperPlaneRight, CheckCircle
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { LocationBadge, VisaBadge, getScoreColor, getMatchClass, numericToGrade } from '@/components/ProcessedCards'
import ResumePreview from '@/components/ResumePreview'

export default function JobDrawer({ drawer, drawerTab, generatingResume, generatingCover, onClose, onSetDrawerTab, onRescoreJob, onRequeueJob, onUpdateJob, onSetToast, onGenerateResume, onGenerateCover }) {
  if (!drawer) return null

  const job = drawer.job
  const drawerLocations = (() => {
    if (job.locations) {
      try { const locs = typeof job.locations === 'string' ? JSON.parse(job.locations) : job.locations; return locs.length ? locs : [job.location] } catch { return [job.location] }
    }
    return [job.location]
  })()

  return (
    <Sheet open={!!drawer} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[min(640px,92vw)] sm:max-w-[640px] overflow-y-auto p-4 pr-12">
        <SheetHeader className="mb-4">
          <div className="flex gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                {/* Overall Score - Primary */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-4xl font-black", getScoreColor(job.overall_score != null ? job.overall_score : job.score))}>
                    {job.overall_score != null ? Math.round(job.overall_score) : job.score}
                  </div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Overall</div>
                </div>
                {/* Fit Score */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-lg font-bold", getScoreColor(job.fit_score != null ? job.fit_score : job.score))}>
                    {job.fit_score != null ? Math.round(job.fit_score) : job.score}
                  </div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Fit</div>
                </div>
                {/* Success Score */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-lg font-bold", getScoreColor(job.success_score != null ? job.success_score : job.score))}>
                    {job.success_score != null ? Math.round(job.success_score) : job.success || '?'}
                  </div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Success</div>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onRescoreJob(job.num)} title="Rescore">
                  <TrendUp className="w-3.5 h-3.5" />
                </Button>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onRequeueJob(job.num)} title="Reprocess from scratch">
                  <Repeat className="w-3.5 h-3.5" />
                </Button>
              </div>
              <SheetTitle className="text-lg">{job.company}</SheetTitle>
              <SheetDescription>{job.role}</SheetDescription>
              <div className="flex flex-wrap gap-1 mt-2">
                {job.industry && <Badge variant="secondary" className="text-[0.55rem] bg-primary/10 text-primary">{job.industry}</Badge>}
                {drawerLocations.map((loc, i) => <LocationBadge key={i} loc={loc} />)}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              <Badge variant="outline" className={cn("uppercase border", getMatchClass(job.match))}>{job.match}</Badge>
              {job.action && (
                <div className="text-[0.6rem] font-semibold px-2 py-1 rounded-lg text-right max-w-[180px]"
                  style={{ background: ['A','A+','A++'].includes(job.score) ? 'rgba(34,197,94,0.12)' : ['B','C'].includes(job.score) ? 'rgba(234,179,8,0.12)' : 'rgba(239,68,68,0.12)', color: ['A','A+','A++'].includes(job.score) ? '#22c55e' : ['B','C'].includes(job.score) ? '#eab308' : '#ef4444' }}>
                  {job.action}
                </div>
              )}
              {job.visa && job.visa !== 'Uncertain' && <VisaBadge visa={job.visa} />}
              {job.work_type && <Badge variant="secondary">{job.work_type}</Badge>}
              {job.apply_time && (
                <Badge variant="outline" className="text-[0.55rem] bg-green-500/10 text-green-500 border-green-500/30 gap-0.5">
                  <PaperPlaneRight className="w-2.5 h-2.5" />Applied
                </Badge>
              )}
              {job.response_status && (
                <Badge variant="outline" className={cn("text-[0.55rem] gap-0.5",
                  job.response_status === 'Interview' ? 'bg-green-500/10 text-green-500 border-green-500/30' :
                  'bg-red-500/10 text-red-500 border-red-500/30'
                )}>
                  {job.response_status === 'Interview' ? <CheckCircle className="w-2.5 h-2.5" /> : null}
                  {job.response_status}
                </Badge>
              )}
            </div>
          </div>
        </SheetHeader>

        <div className="flex gap-2 mb-3">
          <a href={job.url} target="_blank" rel="noreferrer" className="flex-1">
            <Button className="w-full gap-2"><Link className="w-4 h-4" /> Open Job Page</Button>
          </a>
          <Button variant="outline" onClick={() => { navigator.clipboard.writeText(job.url); onSetToast('Copied!'); setTimeout(() => onSetToast(null), 2000) }}>
            Copy URL
          </Button>
        </div>

        {job.apply_reason && (
          <div className="mb-3 p-3 rounded-lg text-sm border"
            style={{
              background: ['Apply Now','Apply Soon'].includes(job.action) ? 'rgba(34,197,94,0.08)' : job.action === 'Consider' ? 'rgba(234,179,8,0.08)' : 'rgba(239,68,68,0.08)',
              borderColor: ['Apply Now','Apply Soon'].includes(job.action) ? 'rgba(34,197,94,0.2)' : job.action === 'Consider' ? 'rgba(234,179,8,0.2)' : 'rgba(239,68,68,0.2)',
              color: ['Apply Now','Apply Soon'].includes(job.action) ? '#4ade80' : job.action === 'Consider' ? '#facc15' : '#f87171',
            }}>
            <div className="text-[0.6rem] uppercase tracking-wider font-semibold mb-1 opacity-70">Why {job.action || 'Apply/Skip'}</div>
            {job.apply_reason}
          </div>
        )}

        <Tabs value={drawerTab} onValueChange={onSetDrawerTab} className="mb-3">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="structured">Structured</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="resume">Resume</TabsTrigger>
            <TabsTrigger value="cover">Cover Letter</TabsTrigger>
          </TabsList>
          {drawerTab === 'resume' && (
            <div className="flex justify-end mt-2">
              <Button variant={drawer.resume ? "outline" : "default"} size="sm" onClick={() => onGenerateResume(job.num)} disabled={generatingResume} className="gap-1.5 h-7 text-xs">
                {generatingResume ? <Spinner className="w-3 h-3 animate-spin" /> : <Repeat className="w-3 h-3" />}
                {generatingResume ? 'Generating...' : drawer.resume ? 'Regenerate Resume' : 'Generate Resume'}
              </Button>
            </div>
          )}
          {drawerTab === 'cover' && (
            <div className="flex justify-end mt-2">
              <Button variant={drawer.coverLetter ? "outline" : "default"} size="sm" onClick={() => onGenerateCover(job.num)} disabled={generatingCover} className="gap-1.5 h-7 text-xs">
                {generatingCover ? <Spinner className="w-3 h-3 animate-spin" /> : <Repeat className="w-3 h-3" />}
                {generatingCover ? 'Generating...' : drawer.coverLetter ? 'Regenerate Cover' : 'Generate Cover Letter'}
              </Button>
            </div>
          )}
        </Tabs>

        {drawerTab === 'details' && <DetailsTab job={job} onUpdateJob={onUpdateJob} />}
        {drawerTab === 'structured' && <StructuredTab job={job} />}
        {drawerTab === 'summary' && <SummaryTab summary={drawer.summary} />}
        {drawerTab === 'resume' && <ResumeTabContent resume={drawer.resume} />}
        {drawerTab === 'cover' && <CoverTabContent coverLetter={drawer.coverLetter} />}
      </SheetContent>
    </Sheet>
  )
}

function DetailsTab({ job, onUpdateJob }) {
  let sd = null; try { sd = job.structured_description ? JSON.parse(job.structured_description) : null } catch {}
  return (
    <div>
      <div className="mb-3 p-3 rounded-lg border border-border/50 bg-muted/30">
        <h4 className="text-[0.6rem] uppercase tracking-wider mb-2 text-primary font-semibold">Application Tracking</h4>
        <div className="grid gap-2">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground w-20 shrink-0">Applied:</label>
            <input type="date" className="h-7 text-xs rounded border border-input bg-background px-2 flex-1"
              value={job.apply_time ? new Date(job.apply_time).toISOString().split('T')[0] : ''}
              onChange={(e) => {
                const val = e.target.value ? new Date(e.target.value + 'T00:00:00').toISOString() : null
                onUpdateJob(job.num, { apply_time: val })
              }} />
            {job.apply_time && <span className="text-[0.55rem] text-green-500 shrink-0">Applied</span>}
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground w-20 shrink-0">Status:</label>
            <Select value={job.response_status || 'none'} onValueChange={(val) => {
              onUpdateJob(job.num, { response_status: val === 'none' ? null : val })
            }}>
              <SelectTrigger className="h-7 text-xs flex-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Response</SelectItem>
                <SelectItem value="Interview">Interview</SelectItem>
                <SelectItem value="Rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {job.response_status && (
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground w-20 shrink-0">Response:</label>
              <input type="date" className="h-7 text-xs rounded border border-input bg-background px-2 flex-1"
                value={job.response_time ? new Date(job.response_time).toISOString().split('T')[0] : ''}
                onChange={(e) => {
                  const val = e.target.value ? new Date(e.target.value + 'T00:00:00').toISOString() : null
                  onUpdateJob(job.num, { response_time: val })
                }} />
            </div>
          )}
        </div>
      </div>
      <ul className="text-sm space-y-1 mb-3 text-muted-foreground">
        <li><b className="text-foreground">Salary:</b> {job.salary}</li>
        {job.company_url && <li><b className="text-foreground">Company Website:</b> <a href={job.company_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{job.company_url}</a></li>}
        {job.linkedin_url && <li><b className="text-foreground">Company LinkedIn:</b> <a href={job.linkedin_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{job.linkedin_url}</a></li>}
        <li><b className="text-foreground">Industry:</b> {job.industry}</li>
        <li><b className="text-foreground">Domain:</b> {job.domain}</li>
        <li><b className="text-foreground">Posted:</b> {job.posted}</li>
        {job.adv_at && <li><b className="text-foreground">Listed:</b> {new Date(job.adv_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</li>}
        {job.see_at && <li><b className="text-foreground">Seen:</b> {new Date(job.see_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</li>}
        <li><b className="text-foreground">Applicants:</b> {job.applicants}</li>
        <li><b className="text-foreground">Visa:</b> {job.visa}</li>
        <li><b className="text-foreground">Work Type:</b> {job.work_type}</li>
        {sd?.company_size && <li><b className="text-foreground">Company Size:</b> {sd.company_size}</li>}
      </ul>
      {sd?.responsibilities?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Key Responsibilities</h4>
          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.requirements?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Requirements</h4>
          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3.5 h-3.5 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.nice_to_have?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Nice to Have</h4>
          <ul className="text-sm space-y-1">{sd.nice_to_have.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Star className="w-3.5 h-3.5 shrink-0 mt-0.5 text-yellow-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.benefits?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Benefits</h4>
          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3.5 h-3.5 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.visa_reason && (
        <div className="mb-3">
          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Visa Assessment</h4>
          <p className="text-sm flex items-start gap-2 text-muted-foreground"><Shield className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{sd.visa_reason}</span></p>
        </div>
      )}
      <div className="mb-3">
        <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Analysis</h4>
        <p className="text-sm text-muted-foreground">{job.notes}</p>
      </div>
    </div>
  )
}

function StructuredTab({ job }) {
  let sd = null; try { sd = job.structured_description ? JSON.parse(job.structured_description) : null } catch {}
  if (!sd) return <div className="text-xs py-4 text-center text-muted-foreground">No structured data available</div>
  return (
    <div>
      {sd.requirements?.length > 0 && (
        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Requirements</h4>
          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3 h-3 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul></div>
      )}
      {sd.responsibilities?.length > 0 && (
        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Responsibilities</h4>
          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3 h-3 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul></div>
      )}
      {sd.benefits?.length > 0 && (
        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Benefits</h4>
          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3 h-3 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul></div>
      )}
    </div>
  )
}

function SummaryTab({ summary }) {
  if (!summary) return <div className="text-xs py-4 text-center text-muted-foreground">No summary available</div>
  return (
    <div>
      <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Summary</h4><p className="text-sm text-muted-foreground">{summary.summary}</p></div>
      <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Stack Required</h4><p className="text-sm text-muted-foreground">{summary.stack}</p></div>
      <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Resume Fit</h4><p className="text-sm text-muted-foreground">{summary.resumeFit}</p></div>
      <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Note</h4>
        <p className="text-sm font-semibold" style={{ color: ['A','A+','A++'].includes(summary.score) ? '#22c55e' : ['B','C'].includes(summary.score) ? '#eab308' : '#ef4444' }}>{summary.note}</p></div>
    </div>
  )
}

function ResumeTabContent({ resume }) {
  return (
    <div>
      {resume && <ResumePreview html={resume.content} />}
      {!resume && (
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <FileText className="w-12 h-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No tailored resume generated yet</p>
        </div>
      )}
    </div>
  )
}

function CoverTabContent({ coverLetter }) {
  return (
    <div>
      {coverLetter && <ResumePreview html={coverLetter.content} />}
      {!coverLetter && (
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <FileText className="w-12 h-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No cover letter generated yet</p>
        </div>
      )}
    </div>
  )
}
