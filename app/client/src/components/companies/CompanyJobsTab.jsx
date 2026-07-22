import { useState, useEffect } from 'react'
import { MapPin, Spinner } from '@phosphor-icons/react'
import { Badge } from '@/components/ui/badge'

export default function CompanyJobsTab({ companyId }) {
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
        <a key={j.num} href={`#jobs`} onClick={() => window.dispatchEvent(new CustomEvent('openJob', { detail: j.num }))}
          className="block p-2 rounded border border-border/50 hover:bg-muted/50 transition">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold">#{j.num}</span>
            <span className="text-xs font-semibold truncate flex-1">{j.role || 'Untitled'}</span>
            {j.score && <Badge variant="secondary" className="text-[0.5rem]">{j.score}</Badge>}
          </div>
          {j.location && <div className="text-[0.55rem] text-muted-foreground mt-0.5"><MapPin className="w-2 h-2 inline mr-0.5" />{j.location}</div>}
        </a>
      ))}
    </div>
  )
}
