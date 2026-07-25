import { useState, useEffect } from 'react'
import { MapPin, Spinner, ArrowSquareOut, ArrowRight, ArrowSquareRight } from '@phosphor-icons/react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export default function CompanyJobsTab({ companyId, companyName, onOpenJob, onNavigateToJob, onViewAllJobs }) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/companies/${companyId}/jobs`)
      .then(r => r.json())
      .then(data => { setJobs(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [companyId])

  if (loading) return <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground"><Spinner className="w-3 h-3 animate-spin" /> Loading jobs...</div>

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground">{jobs.length} linked job{jobs.length !== 1 ? 's' : ''}</span>
      </div>
      {jobs.length === 0 && (
        <div className="text-center py-6 text-xs text-muted-foreground">No jobs linked to this company yet.</div>
      )}
      {jobs.map(j => (
        <div key={j.num} className="flex items-center gap-1 p-2 rounded border border-border/50 hover:bg-muted/50 transition group">
          <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onOpenJob?.(j.num)}>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold">#{j.num}</span>
              <span className="text-xs font-semibold truncate flex-1">{j.role || 'Untitled'}</span>
              {j.score && <Badge variant="secondary" className="text-[0.5rem]">{j.score}</Badge>}
            </div>
            {j.location && <div className="text-[0.55rem] text-muted-foreground mt-0.5"><MapPin className="w-2 h-2 inline mr-0.5" />{j.location}</div>}
          </div>
          <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition">
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => onOpenJob?.(j.num)} title="Open job drawer">
              <ArrowSquareOut className="w-3 h-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => onNavigateToJob?.(j.num)} title="Go to Jobs page">
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
