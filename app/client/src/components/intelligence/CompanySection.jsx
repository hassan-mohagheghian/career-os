import { useState, useEffect } from 'react'
import {
  Buildings, IdentificationCard, Globe, ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function CompanySection({ analysis, refreshing, onRefresh, onOpenDrawer }) {
  const visaCompanies = analysis.visa_companies || []
  const cities = analysis.cities || []
  const [allJobs, setAllJobs] = useState([])

  useEffect(() => {
    fetch('/api/jobs?limit=9999&sort_by=created_at&sort_dir=desc')
      .then(r => r.json())
      .then(d => setAllJobs(d.jobs || []))
      .catch(() => {})
  }, [])

  // Build company rankings from all jobs
  const companyMap = {}
  allJobs.forEach(j => {
    if (!companyMap[j.company]) {
      companyMap[j.company] = { company: j.company, jobs: [], totalFit: 0, totalSuccess: 0, totalOverall: 0, visa: j.visa, location: j.location }
    }
    companyMap[j.company].jobs.push(j)
    companyMap[j.company].totalFit += (j.fit_score || 0)
    companyMap[j.company].totalSuccess += (j.success_score || 0)
    companyMap[j.company].totalOverall += (j.overall_score || 0)
  })

  const companyRankings = Object.values(companyMap)
    .map(c => ({
      ...c,
      avgFit: c.jobs.length ? Math.round(c.totalFit / c.jobs.length) : 0,
      avgSuccess: c.jobs.length ? Math.round(c.totalSuccess / c.jobs.length) : 0,
      avgOverall: c.jobs.length ? Math.round(c.totalOverall / c.jobs.length) : 0,
      matchCount: c.jobs.filter(j => j.match === 'High').length,
    }))
    .sort((a, b) => b.avgOverall - a.avgOverall)
    .slice(0, 15)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Company Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Company Rankings */}
          {companyRankings.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Buildings className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Company Rankings</h3>
                <Badge variant="secondary" className="text-[0.5rem]">{companyRankings.length} companies</Badge>
              </div>
              <div className="space-y-1.5">
                {companyRankings.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 text-[0.6rem] p-2 rounded hover:bg-muted transition">
                    <div className="w-6 text-center font-bold text-primary">#{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold">{c.company}</div>
                      <div className="text-muted-foreground">{c.jobs.length} roles · {c.location}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5">F:{c.avgFit}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5">S:{c.avgSuccess}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-purple-500/15 text-purple-500">O:{c.avgOverall}</Badge>
                    </div>
                    {c.matchCount > 0 && <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500">{c.matchCount} high</Badge>}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Visa Companies */}
          {visaCompanies.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <IdentificationCard className="w-5 h-5 text-purple-500" />
                <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
              </div>
              <div className="space-y-1.5">
                {visaCompanies.slice(0, 8).map((j, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{j.company}</span>
                    <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{j.visa}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Cities */}
          {cities.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-5 h-5 text-primary" />
                <h3 className="font-extrabold text-sm">Top Cities</h3>
              </div>
              <div className="space-y-1.5">
                {cities.slice(0, 6).map((c, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                    <span className="font-semibold">{c.name}</span>
                    <span className="text-muted-foreground">{c.jobs} jobs ({c.percentage}%)</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
