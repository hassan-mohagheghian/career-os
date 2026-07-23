import {
  Buildings, IdentificationCard, Star, Wrench, Globe, Users, ArrowsClockwise, Trophy
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

function CompanyCard({ company, type }) {
  const visaColors = {
    'BEST': 'bg-green-500/15 text-green-500 border-green-500/30',
    'Strong': 'bg-green-400/15 text-green-400 border-green-400/30',
    'Good': 'bg-yellow-500/15 text-yellow-500 border-yellow-500/30',
  }
  return (
    <Card className="p-3 transition hover:border-primary">
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm">{company.company || company.name}</span>
        {company.fitScore && (
          <Badge variant="outline" className="text-[0.55rem]">{company.fitScore}%</Badge>
        )}
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

export default function CompaniesSection({ data, refreshing, onRefresh }) {
  const companies = data?.companies || {}
  const productCo = companies.productCompanies || []
  const recruitingCo = companies.recruitingCompanies || []
  const topTargets = companies.topTargets || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Company Intelligence</h3>
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
              <Card key={i} className="p-3 text-center transition hover:border-primary border-l-3 border-l-yellow-500">
                <div className="text-lg font-extrabold text-yellow-500">#{t.rank}</div>
                <div className="font-bold text-xs mt-1">{t.company}</div>
                <div className="text-[0.55rem] text-muted-foreground mt-0.5">{t.fit}% fit</div>
                <Badge variant="secondary" className="text-[0.45rem] h-3 mt-1">{t.visa}</Badge>
                <div className="text-[0.5rem] text-muted-foreground mt-1 line-clamp-2">{t.reason}</div>
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
              <CompanyCard key={i} company={co} type="product" />
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
              <CompanyCard key={i} company={co} type="recruiting" />
            )) : (
              <div className="text-xs text-muted-foreground text-center py-4">No recruiting companies analyzed</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
