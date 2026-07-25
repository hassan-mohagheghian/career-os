import { useState, useEffect } from 'react'
import {
  Buildings, IdentificationCard, Star, Wrench, Globe, Users, ArrowsClockwise, Trophy, Plus, ArrowRight, Clock
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'

function formatTimeAgo(ts) {
  if (!ts) return ''
  const diffMs = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return days < 7 ? `${days}d ago` : new Date(ts).toLocaleDateString()
}

function CompanyCard({ company, type, onOpenCompany, onAddCompany, existsInSystem }) {
  const visaColors = {
    'BEST': 'bg-green-500/15 text-green-500 border-green-500/30',
    'Strong': 'bg-green-400/15 text-green-400 border-green-400/30',
    'Good': 'bg-yellow-500/15 text-yellow-500 border-yellow-500/30',
  }
  const companyName = company.company || company.name

  return (
    <Card className={cn("p-3 transition hover:border-primary group relative")}>
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm">{companyName}</span>
        <div className="flex items-center gap-1">
          {company.fitScore && (
            <Badge variant="outline" className="text-[0.55rem]">{company.fitScore}%</Badge>
          )}
          {/* Show Add button on hover if company not in system */}
          {!existsInSystem && onAddCompany && (
            <Button
              size="sm"
              variant="default"
              onClick={(e) => {
                e.stopPropagation()
                onAddCompany(companyName)
              }}
              className="h-5 text-[0.5rem] gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Plus className="w-2.5 h-2.5" /> Add
            </Button>
          )}
          {/* Show Open button on hover if company exists in system */}
          {existsInSystem && onOpenCompany && (
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                onOpenCompany(companyName)
              }}
              className="h-5 text-[0.5rem] gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ArrowRight className="w-2.5 h-2.5" /> Open
            </Button>
          )}
        </div>
      </div>
      {type === 'product' ? (
        <div className="space-y-1.5 text-[0.6rem] text-muted-foreground">
          <div className="flex items-center gap-1">
            <IdentificationCard className="w-3 h-3" />
            <span>Visa: </span>
            <Badge variant="secondary" className={cn("text-[0.45rem] h-3", visaColors[company.visaStrength] || 'bg-gray-500/15 text-gray-400')}>
              {company.visaStrength}
            </Badge>
          </div>
          {company.engineeringCulture && <div><b>Culture:</b> {company.engineeringCulture}</div>}
          {company.technologyAlignment && <div><b>Tech:</b> {company.technologyAlignment}</div>}
          {company.reason && <div className="text-primary text-[0.55rem]">{company.reason}</div>}
        </div>
      ) : (
        <div className="space-y-1.5 text-[0.6rem] text-muted-foreground">
          <div className="flex items-center gap-3">
            <span><b>Jobs:</b> {company.relevantJobs}</span>
            <span><b>International:</b> {company.internationalHiring}</span>
          </div>
          {company.techSpecialization && <div><b>Specialization:</b> {company.techSpecialization}</div>}
          {company.reason && <div className="text-primary text-[0.55rem]">{company.reason}</div>}
        </div>
      )}
    </Card>
  )
}

export default function CompaniesSection({ data, refreshing, onRefresh, onOpenCompany, onAddCompany, status }) {
  const companies = data?.companies || {}
  const productCo = companies.productCompanies || []
  const recruitingCo = companies.recruitingCompanies || []
  const topTargets = companies.topTargets || []
  const [existingCompanies, setExistingCompanies] = useState(new Set())

  // Fetch existing company names to check which ones are in the system
  useEffect(() => {
    fetch('/api/companies')
      .then(r => r.json())
      .then(list => {
        const names = new Set((Array.isArray(list) ? list : []).map(c => c.name?.toLowerCase()))
        setExistingCompanies(names)
      })
      .catch(() => {})
  }, [])

  const checkExists = (name) => existingCompanies.has(name?.toLowerCase())

  // Helper to find company ID by name
  const findAndOpenCompany = async (name) => {
    if (!onOpenCompany || !name) return
    try {
      const res = await fetch(`/api/companies?search=${encodeURIComponent(name)}`)
      const list = await res.json()
      const match = list.find(c => c.name?.toLowerCase() === name.toLowerCase())
      if (match) {
        onOpenCompany(match.id)
      }
    } catch {
      onOpenCompany(name)
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="font-extrabold text-sm">Company Intelligence</h3>
          {status?.companies?.lastRun && (
            <span className="text-[0.5rem] text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />{formatTimeAgo(status.companies.lastRun)}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.companies} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.companies && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Top Targets */}
      {topTargets.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Trophy className="w-5 h-5 text-yellow-500" />
            <h4 className="font-extrabold text-sm">Top Targets</h4>
          </div>
          <div className="grid grid-cols-5 gap-3">
            {topTargets.map((t, i) => (
              <Card
                key={i}
                className="p-3 text-center transition hover:border-primary border-l-3 border-l-yellow-500 group relative cursor-pointer"
                onClick={() => {
                  if (checkExists(t.company)) {
                    findAndOpenCompany(t.company)
                  } else if (onAddCompany) {
                    onAddCompany(t.company)
                  }
                }}
              >
                <div className="text-lg font-extrabold text-yellow-500">#{t.rank}</div>
                <div className="font-bold text-xs mt-1">{t.company}</div>
                <div className="text-[0.55rem] text-muted-foreground mt-0.5">{t.fit}% fit</div>
                <Badge variant="secondary" className="text-[0.45rem] h-3 mt-1">{t.visa}</Badge>
                <div className="text-[0.5rem] text-muted-foreground mt-1 line-clamp-2">{t.reason}</div>
                {!checkExists(t.company) && onAddCompany && (
                  <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Badge variant="default" className="text-[0.4rem] h-3.5 bg-primary gap-0.5">
                      <Plus className="w-2 h-2" /> Add
                    </Badge>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* Product Companies */}
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Buildings className="w-5 h-5 text-primary" />
            <h4 className="font-extrabold text-sm">Product Companies</h4>
            <Badge variant="secondary" className="text-[0.5rem]">{productCo.length}</Badge>
          </div>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {productCo.length > 0 ? productCo.map((co, i) => (
              <CompanyCard
                key={i}
                company={co}
                type="product"
                onOpenCompany={findAndOpenCompany}
                onAddCompany={onAddCompany}
                existsInSystem={checkExists(co.company || co.name)}
              />
            )) : (
              <div className="text-xs text-muted-foreground text-center py-4">No product companies analyzed</div>
            )}
          </div>
        </Card>

        {/* Recruiting Companies */}
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-cyan-500" />
            <h4 className="font-extrabold text-sm">Recruiting / Staffing</h4>
            <Badge variant="secondary" className="text-[0.5rem]">{recruitingCo.length}</Badge>
          </div>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {recruitingCo.length > 0 ? recruitingCo.map((co, i) => (
              <CompanyCard
                key={i}
                company={co}
                type="recruiting"
                onOpenCompany={findAndOpenCompany}
                onAddCompany={onAddCompany}
                existsInSystem={checkExists(co.company || co.name)}
              />
            )) : (
              <div className="text-xs text-muted-foreground text-center py-4">No recruiting companies analyzed</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
