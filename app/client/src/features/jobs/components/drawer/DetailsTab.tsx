import { Lightning, ListChecks, Star, Gift, Shield } from '@phosphor-icons/react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { TabHeader } from '@/shared/components/DrawerComponents'

export default function DetailsTab({ job, onUpdateJob }) {
  let sd = null; try { sd = job.structured_description ? JSON.parse(job.structured_description) : null } catch {}
  return (
    <div>
      <div className="mb-3 p-3 rounded-lg border border-border/50 bg-muted/30">
        <TabHeader title="Application Tracking" className="mb-2 font-semibold" />
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
          <TabHeader title="Key Responsibilities" />
          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.requirements?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Requirements" />
          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3.5 h-3.5 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.nice_to_have?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Nice to Have" />
          <ul className="text-sm space-y-1">{sd.nice_to_have.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Star className="w-3.5 h-3.5 shrink-0 mt-0.5 text-yellow-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.benefits?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Benefits" />
          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3.5 h-3.5 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd?.visa_reason && (
        <div className="mb-3">
          <TabHeader title="Visa Assessment" />
          <p className="text-sm flex items-start gap-2 text-muted-foreground"><Shield className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{sd.visa_reason}</span></p>
        </div>
      )}
      <div className="mb-3">
        <TabHeader title="Analysis" />
        <p className="text-sm text-muted-foreground">{job.notes}</p>
      </div>
    </div>
  )
}
