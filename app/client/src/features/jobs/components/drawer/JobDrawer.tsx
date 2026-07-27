import { useState, useEffect } from 'react'
import {
  TrendUp, Repeat, Link, Lightning, ListChecks, Star, Gift, Shield,
  FileText, Spinner, PaperPlaneRight, CheckCircle, Buildings, MapPin, X, ArrowSquareOut, ArrowRight, Clock, CaretDown, CaretRight
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/shared/ui/collapsible'
import { AppDrawer, TabHeader } from '@/shared/components/DrawerComponents'
import { LocationBadge, VisaBadge, getScoreColor, getMatchClass } from '@/shared/components/ProcessedCards'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import { useLocalHistory } from '@/shared/hooks'
import DetailsTab from './DetailsTab'
import StructuredTab from './StructuredTab'
import SummaryTab from './SummaryTab'
import DocumentsTab from './DocumentsTab'
import CompanyTab from './CompanyTab'

export default function JobDrawer({ drawer, drawerTab, activeGens, companies, onClose, onSetDrawerTab, onRescoreJob, onRequeueJob, onUpdateJob, onSetToast, onGenerateResume, onGenerateCover, onCancelGeneration, onLinkCompany, onOpenCompany, onNavigateToCompany }) {
  const [showProcessing, setShowProcessing] = useState(false)
  const { items: localHistory, refresh } = useLocalHistory({
    context: 'job',
    job_num: drawer?.job?.num,
  })

  const processingHistory = localHistory.filter(h => h.source === 'job-processing')

  useEffect(() => {
    refresh()
  }, [drawer]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!drawer) return null

  const job = drawer.job
  const drawerLocations = (() => {
    if (job.locations) {
      try { const locs = typeof job.locations === 'string' ? JSON.parse(job.locations) : job.locations; return locs.length ? locs : [job.location] } catch { return [job.location] }
    }
    return [job.location]
  })()

  return (
    <AppDrawer open={!!drawer} onOpenChange={(open) => !open && onClose()}>
      <div className="p-6 pb-3">
          <div className="flex gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                {/* Overall Score - Primary */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-4xl font-black", getScoreColor(job.overall_score != null ? job.overall_score : job.score))}>
                    {job.overall_score != null ? Math.round(job.overall_score) : job.score}
                  </div>
                  <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Overall</div>
                </div>
                {/* Fit Score */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-lg font-bold", getScoreColor(job.fit_score != null ? job.fit_score : job.score))}>
                    {job.fit_score != null ? Math.round(job.fit_score) : job.score}
                  </div>
                  <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Fit</div>
                </div>
                {/* Success Score */}
                <div className="flex flex-col items-center">
                  <div className={cn("text-lg font-bold", getScoreColor(job.success_score != null ? job.success_score : job.score))}>
                    {job.success_score != null ? Math.round(job.success_score) : job.success || '?'}
                  </div>
                  <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Success</div>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onRescoreJob(job.num)} title="Rescore">
                  <TrendUp className="w-3.5 h-3.5" />
                </Button>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onRequeueJob(job.num)} title="Reprocess from scratch">
                  <Repeat className="w-3.5 h-3.5" />
                </Button>
              </div>
              <div className="text-lg font-semibold flex items-center gap-2">
                {job.company}
                {job.linked_company && (
                  <button onClick={() => onOpenCompany(job.linked_company.id)}
                    className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-2xs font-semibold bg-primary/15 text-primary border border-primary/30 hover:bg-primary/25 transition">
                    <Buildings className="w-2 h-2" />{job.linked_company.name || 'Company'}
                  </button>
                )}
              </div>
              <div className="text-sm text-muted-foreground">{job.role}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {job.industry && <Badge variant="secondary" className="text-2xs bg-primary/10 text-primary">{job.industry}</Badge>}
                {drawerLocations.map((loc, i) => <LocationBadge key={i} loc={loc} />)}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              <Badge variant="outline" className={cn("uppercase border", getMatchClass(job.match))}>{job.match}</Badge>
              {job.action && (
                <div className="text-2xs font-semibold px-2 py-1 rounded-lg text-right max-w-[180px]"
                  style={{ background: ['A','A+','A++'].includes(job.score) ? 'rgba(34,197,94,0.12)' : ['B','C'].includes(job.score) ? 'rgba(234,179,8,0.12)' : 'rgba(239,68,68,0.12)', color: ['A','A+','A++'].includes(job.score) ? '#22c55e' : ['B','C'].includes(job.score) ? '#eab308' : '#ef4444' }}>
                  {job.action}
                </div>
              )}
              {job.visa && job.visa !== 'Uncertain' && <VisaBadge visa={job.visa} />}
              {job.work_type && <Badge variant="secondary">{job.work_type}</Badge>}
              {job.apply_time && (
                <Badge variant="outline" className="text-2xs bg-green-500/10 text-green-500 border-green-500/30 gap-0.5">
                  <PaperPlaneRight className="w-2.5 h-2.5" />Applied
                </Badge>
              )}
              {job.response_status && (
                <Badge variant="outline" className={cn("text-2xs gap-0.5",
                  job.response_status === 'Interview' ? 'bg-green-500/10 text-green-500 border-green-500/30' :
                  'bg-red-500/10 text-red-500 border-red-500/30'
                )}>
                  {job.response_status === 'Interview' ? <CheckCircle className="w-2.5 h-2.5" /> : null}
                  {job.response_status}
                </Badge>
              )}
            </div>
          </div>

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
            <div className="text-2xs uppercase tracking-wider font-semibold mb-1 opacity-70">Why {job.action || 'Apply/Skip'}</div>
            {job.apply_reason}
          </div>
        )}

        {/* Processing History - Collapsible */}
        {processingHistory.length > 0 && (
          <Collapsible open={showProcessing} onOpenChange={setShowProcessing}>
            <div className="mb-3">
              <CollapsibleTrigger asChild>
                <button className="flex items-center gap-1.5 text-2xs font-semibold text-muted-foreground hover:text-foreground transition w-full text-left">
                  {showProcessing ? <CaretDown className="w-3 h-3" /> : <CaretRight className="w-3 h-3" />}
                  <Clock className="w-3 h-3" />
                  Processing History
                  <Badge variant="secondary" className="ml-auto text-2xs h-4">{processingHistory.length}</Badge>
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-1.5 space-y-0.5 pl-1">
                {processingHistory.map(h => (
                  <GenerationHistoryItem key={`${h.source}-${h.id}`} item={h} compact />
                ))}
              </CollapsibleContent>
            </div>
          </Collapsible>
        )}

        <Tabs value={drawerTab} onValueChange={onSetDrawerTab} className="mb-3">
          <TabsList className="bg-muted">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="structured">Structured</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="company">Company</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>
        </Tabs>

        {drawerTab === 'details' && <DetailsTab job={job} onUpdateJob={onUpdateJob} />}
        {drawerTab === 'structured' && <StructuredTab job={job} />}
        {drawerTab === 'summary' && <SummaryTab summary={drawer.summary} />}
        {drawerTab === 'company' && <CompanyTab job={job} companies={companies || []} onLinkCompany={onLinkCompany} onSetToast={onSetToast} onOpenCompany={onOpenCompany} onNavigateToCompany={onNavigateToCompany} onClose={onClose} />}
        {drawerTab === 'documents' && <DocumentsTab job={job} resume={drawer.resume} coverLetter={drawer.coverLetter} activeGens={activeGens} onGenerateResume={onGenerateResume} onGenerateCover={onGenerateCover} onCancelGeneration={onCancelGeneration} />}
      </div>
    </AppDrawer>
  )
}
