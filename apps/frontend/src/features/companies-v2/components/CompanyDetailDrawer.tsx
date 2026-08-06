'use client'

import { useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { CircleNotch, MapPin, Users, Briefcase, LinkSimple, Repeat, Trash } from '@phosphor-icons/react'
import type { CompanyDetail, CompanyIntelligence, CompanyIntelligenceScores } from '@/entities/company/types'
import { useCompanyQuery } from '@/entities/company/hooks'
import CompanyJobsTab from '@/features/companies/components/CompanyJobsTab'
import NotesLinksReadOnly from '@/shared/components/NotesLinksReadOnly'
import { CompanyGradeBadge } from './CompanyGradeBadge'
import { CompanyScoreCard } from './CompanyScoreCard'
import { RelateCompanyDialog } from './RelateCompanyDialog'
import { gradeForScore } from '@/shared/lib/grade'

const COMPANY_TYPE_LABELS: Record<string, string> = {
  PRODUCT_COMPANY: 'Product Company',
  RECRUITING_AGENCY: 'Recruiting Agency',
  STAFFING_COMPANY: 'Staffing Company',
  CONSULTING_COMPANY: 'Consulting Company',
  UNKNOWN: 'Unknown',
}

function formatCompanyType(type: string | null | undefined) {
  return (type && COMPANY_TYPE_LABELS[type]) || type || 'Unknown'
}

function isRecruiterType(type: string | null | undefined) {
  return type === 'RECRUITING_AGENCY' || type === 'STAFFING_COMPANY'
}

interface CompanyDetailDrawerProps {
  companyId: string | null
  onOpenChange: (id: string | null) => void
  onDelete: (id: string) => void
  onReprocess: (id: string) => void
  onRelate: (companyId: string, mainCompanyId: string | null) => void
  relatePending: boolean
  onOpenJob?: (id: string) => void
  onNavigateToJob?: (id: string) => void
  onViewAllJobs?: (name: string) => void
}

export function CompanyDetailDrawer({
  companyId, onOpenChange, onDelete, onReprocess, onRelate, relatePending, onOpenJob, onNavigateToJob, onViewAllJobs,
}: CompanyDetailDrawerProps) {
  const { data: company, isLoading, isError } = useCompanyQuery(companyId)
  const [relateDialogOpen, setRelateDialogOpen] = useState(false)

  return (
    <Sheet open={!!companyId} onOpenChange={(open) => { if (!open) onOpenChange(null) }}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold">Company Details</SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0 min-w-0">
          {isLoading && (
            <div className="flex items-center justify-center h-40">
              <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
            </div>
          )}
          {isError && (
            <div className="flex items-center justify-center h-40">
              <p className="text-sm text-red-500">Unable to load company details.</p>
            </div>
          )}
          {company && !isLoading && (
            <CompanyDetailContent
              company={company}
              onDelete={onDelete}
              onReprocess={onReprocess}
              onOpenJobsRelation={() => setRelateDialogOpen(true)}
              onOpenJob={onOpenJob}
              onNavigateToJob={onNavigateToJob}
              onViewAllJobs={onViewAllJobs}
            />
          )}
        </ScrollArea>
      </SheetContent>
      <RelateCompanyDialog
        company={company ?? null}
        open={relateDialogOpen}
        onOpenChange={setRelateDialogOpen}
        onRelate={onRelate}
        pending={relatePending}
      />
    </Sheet>
  )
}

interface CompanyDetailContentProps {
  company: CompanyDetail
  onDelete: (id: string) => void
  onReprocess: (id: string) => void
  onOpenJobsRelation: () => void
  onOpenJob?: (id: string) => void
  onNavigateToJob?: (id: string) => void
  onViewAllJobs?: (name: string) => void
}

function CompanyDetailContent({
  company,
  onDelete, onReprocess, onOpenJobsRelation, onOpenJob, onNavigateToJob, onViewAllJobs,
}: CompanyDetailContentProps) {
  const intel = company.intelligence
  const scores = intel?.scores || {}
  const fitScore = scores.company_fit_score ?? null
  const successScore = scores.company_success_score ?? null
  const overallScore = scores.company_overall_score ?? null
  const overallGrade = overallScore != null ? gradeForScore(overallScore) : (scores.overall_grade || scores.fit_grade || null)

  return (
    <div className="space-y-4 px-4 py-4 min-w-0">
      <div className="flex items-center gap-3 mb-1">
        <CompanyGradeBadge grade={overallGrade} className="w-10 h-8 text-sm" />
        {fitScore != null && <CompanyScoreCard label="Fit" value={fitScore} />}
        {successScore != null && <CompanyScoreCard label="Success" value={successScore} />}
        {overallScore != null && <CompanyScoreCard label="Overall" value={overallScore} />}
      </div>
      <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
        {company.logo_url && <img src={company.logo_url} alt="" className="w-5 h-5 rounded" />}
        {company.name || 'Unknown Company'}
      </h2>
      <p className="text-sm text-muted-foreground -mt-2">{company.industry || 'Technology'}</p>
      <div className="flex flex-wrap gap-1 -mt-1">
        {(company.city || company.country) && (
          <Badge variant="secondary" className="text-2xs">
            <MapPin className="w-2.5 h-2.5 mr-1" />{[company.city, company.country].filter(Boolean).join(', ')}
          </Badge>
        )}
        {company.company_size && (
          <Badge variant="secondary" className="text-2xs">
            <Users className="w-2.5 h-2.5 mr-1" />{company.company_size}
          </Badge>
        )}
        {company.company_type && (
          <Badge variant="secondary" className="text-2xs">{formatCompanyType(company.company_type)}</Badge>
        )}
        {!!company.job_count && company.job_count > 0 && (
          <Badge variant="secondary" className="text-2xs bg-primary/10 text-primary">
            <Briefcase className="w-2.5 h-2.5 mr-1" />{company.job_count} job{company.job_count !== 1 ? 's' : ''}
          </Badge>
        )}
      </div>

      <div className="flex items-center justify-between rounded-lg border border-border/40 bg-muted/10 px-3 py-2">
        <div className="flex items-center gap-2 min-w-0">
          <LinkSimple className="w-3.5 h-3.5 text-primary shrink-0" />
          {company.is_alias && company.main_company ? (
            <span className="text-xs text-muted-foreground truncate">
              Part of <span className="font-semibold text-foreground">{company.main_company.name}</span>
            </span>
          ) : company.alias_count && company.alias_count > 0 ? (
            <span className="text-xs text-muted-foreground truncate">
              {company.alias_count} related compan{company.alias_count === 1 ? 'y' : 'ies'}
            </span>
          ) : (
            <span className="text-xs text-muted-foreground truncate">No related companies</span>
          )}
        </div>
        <Button variant="outline" size="sm" className="h-7 text-2xs shrink-0" onClick={onOpenJobsRelation}>
          Manage
        </Button>
      </div>

      <CompanyRecommendationSection intel={intel} />

      <CompanyIntelligenceSection company={company} intel={intel} isRecruiter={isRecruiterType(company.company_type)} />

      <CompanyScoresSection intel={intel} />

      {company.jobs && company.jobs.length > 0 && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            <Briefcase className="w-3 h-3 inline mr-1 text-primary" />Linked Jobs
          </p>
          <CompanyJobsTab
            companyId={company.id}
            companyName={company.name}
            jobs={company.jobs || []}
            onOpenJob={onOpenJob}
            onNavigateToJob={onNavigateToJob}
            onViewAllJobs={onViewAllJobs}
          />
        </div>
      )}

      <NotesLinksReadOnly notes={company.notes} links={company.links} heading="Notes & Links" />

      <div className="flex flex-wrap items-center gap-2 border-t border-border/40 pt-3">
        {!!company.job_count && company.job_count > 0 && onViewAllJobs && (
          <Button variant="outline" size="sm" className="gap-1 h-7 text-2xs" onClick={() => onViewAllJobs(company.name)}>
            <Briefcase className="w-3 h-3" /> View All Jobs
          </Button>
        )}
        {company.website && (
          <a href={company.website} target="_blank" rel="noreferrer">
            <Button variant="outline" size="sm" className="gap-1 h-7 text-2xs">
              <LinkSimple className="w-3 h-3" /> Website
            </Button>
          </a>
        )}
        <div className="flex-1" />
        <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs" onClick={() => onReprocess(company.id)}>
          <Repeat className="w-3 h-3" /> Reprocess
        </Button>
        <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs text-destructive" onClick={() => onDelete(company.id)}>
          <Trash className="w-3 h-3" /> Delete
        </Button>
      </div>
    </div>
  )
}

function CompanyRecommendationSection({ intel }: { intel: CompanyIntelligence | null | undefined }) {
  const recommendation = intel?.recommendation
  if (!recommendation || typeof recommendation !== 'object' || Object.keys(recommendation).length === 0) {
    return null
  }

  const priority = recommendation.priority
  const observation = recommendation.observation
  const evidence = recommendation.evidence
  const impact = recommendation.impact
  const action = recommendation.action
  const idealRole = recommendation.ideal_role
  const timing = recommendation.timing

  const Field = ({ label, value }: { label: string; value: unknown }) => (
    value ? (
      <div className="flex items-start justify-between gap-4 py-1.5">
        <span className="text-2xs text-muted-foreground uppercase tracking-wide shrink-0">{label}</span>
        <span className="text-xs text-foreground text-right break-words">{typeof value === 'string' ? value : JSON.stringify(value)}</span>
      </div>
    ) : null
  )

  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center gap-2 mb-1">
        <CompanyGradeBadge grade={typeof priority === 'string' ? priority : null} className="w-8 h-6 text-xs" />
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">Recommendation</p>
      </div>
      {typeof observation === 'string' && observation && (
        <p className="text-xs text-foreground whitespace-pre-wrap mb-1">{observation}</p>
      )}
      {typeof action === 'string' && action && (
        <p className="text-xs text-primary font-medium mb-2">{action}</p>
      )}
      <Field label="Evidence" value={evidence} />
      <Field label="Impact" value={impact} />
      <Field label="Ideal Role" value={idealRole} />
      <Field label="Timing" value={timing} />
    </div>
  )
}

function CompanyIntelligenceSection({ company, intel, isRecruiter }: {
  company: CompanyDetail
  intel: CompanyIntelligence | null | undefined
  isRecruiter: boolean
}) {
  const Section = ({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) => (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
        {icon}{title}
      </p>
      {children}
    </div>
  )
  const Field = ({ label, value }: { label: string; value: unknown }) => (
    value ? (
      <div className="flex items-start justify-between gap-4 py-1.5">
        <span className="text-2xs text-muted-foreground uppercase tracking-wide shrink-0">{label}</span>
        <span className="text-xs text-foreground text-right break-words">{typeof value === 'string' ? value : JSON.stringify(value)}</span>
      </div>
    ) : null
  )
  const TagList = ({ items }: { items: unknown[] }) => (
    <div className="flex flex-wrap gap-1 mt-1">
      {items.map((item, i) => (
        <span key={i} className="inline-flex items-center rounded-md border border-border/60 px-2 py-0.5 text-2xs text-muted-foreground">
          {typeof item === 'string' ? item : JSON.stringify(item)}
        </span>
      ))}
    </div>
  )

  if (!intel) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <p className="text-sm text-muted-foreground">No intelligence data yet. Processing may be in progress.</p>
      </div>
    )
  }

  const overview = intel.overview || {}
  const culture = intel.culture_analysis || {}
  const international = intel.international_analysis || {}
  const career = intel.career_analysis || {}
  const benefits = intel.benefits_analysis || {}
  const visa = intel.visa_analysis || {}
  const tech = intel.technology_analysis || {}

  const OverviewSection = () => (
    <Section title="Company Overview" icon={<Briefcase className="w-3 h-3 text-primary" />}>
      <Field label="Products" value={overview.products} />
      <Field label="Founded" value={overview.founded} />
      <Field label="Headquarters" value={overview.headquarters} />
      <Field label="Size" value={overview.size || company.company_size} />
      {Array.isArray(overview.countries) && overview.countries.length > 0 && (
        <div className="py-1.5"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Countries</span><TagList items={overview.countries} /></div>
      )}
      <Field label="Market Position" value={overview.market_position} />
      <Field label="Funding Summary" value={overview.funding_summary} />
      <Field label="Growth Trajectory" value={overview.growth_trajectory} />
    </Section>
  )

  const VisaSection = () => (
    <Section title="Visa & Relocation Signals" icon={<LinkSimple className="w-3 h-3 text-emerald-500" />}>
      <Field label="Sponsorship History" value={visa.sponsorship_history} />
      <Field label="International Hiring" value={visa.international_hiring} />
      <Field label="English First" value={visa.english_first} />
      {Array.isArray(visa.positive_signals) && visa.positive_signals.length > 0 && (
        <div className="py-1.5">
          <p className="text-2xs font-medium text-green-500">Positive Signals</p>
          {visa.positive_signals.map((s, i) => <p key={i} className="text-xs mt-0.5">- {typeof s === 'string' ? s : JSON.stringify(s)}</p>)}
        </div>
      )}
      {Array.isArray(visa.risks) && visa.risks.length > 0 && (
        <div className="py-1.5">
          <p className="text-2xs font-medium text-red-400">Risks</p>
          {visa.risks.map((r, i) => <p key={i} className="text-xs mt-0.5">- {typeof r === 'string' ? r : JSON.stringify(r)}</p>)}
        </div>
      )}
    </Section>
  )

  const WorkEnvironmentSection = () => (
    <Section title="Work Environment" icon={<Users className="w-3 h-3 text-green-500" />}>
      <Field label="Remote Policy" value={benefits.remote_policy} />
      <Field label="Hybrid Policy" value={benefits.hybrid_details || benefits.hybrid_policy} />
      <Field label="Vacation" value={benefits.vacation} />
      <Field label="Learning Budget" value={benefits.learning_budget} />
      <Field label="Equipment" value={benefits.equipment} />
      {Array.isArray(benefits.benefits) && benefits.benefits.length > 0 && (
        <div className="py-1.5"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Benefits</span><TagList items={benefits.benefits} /></div>
      )}
    </Section>
  )

  const RecruiterOverviewSection = () => (
    <Section title="Recruiter Overview" icon={<Briefcase className="w-3 h-3 text-primary" />}>
      <Field label="Founded" value={overview.founded} />
      <Field label="Headquarters" value={overview.headquarters} />
      <Field label="Size" value={overview.size || company.company_size} />
      {Array.isArray(overview.countries) && overview.countries.length > 0 && (
        <div className="py-1.5"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Countries</span><TagList items={overview.countries} /></div>
      )}
      <Field label="Market Position" value={overview.market_position} />
      <Field label="Funding Summary" value={overview.funding_summary} />
      <Field label="Growth Trajectory" value={overview.growth_trajectory} />
    </Section>
  )

  const InternationalHiringSection = () => (
    <Section title="International Hiring" icon={<GlobeIcon />}>
      <Field label="English Usage" value={international.english_usage} />
      <Field label="International Employees" value={international.international_employees} />
      <Field label="Visa Sponsorship" value={visa.sponsorship_history} />
      <Field label="International Hiring" value={visa.international_hiring} />
      {Array.isArray(visa.positive_signals) && visa.positive_signals.length > 0 && (
        <div className="py-1.5">
          <p className="text-2xs font-medium text-green-500">Positive Signals</p>
          {visa.positive_signals.map((s, i) => <p key={i} className="text-xs mt-0.5">- {typeof s === 'string' ? s : JSON.stringify(s)}</p>)}
        </div>
      )}
    </Section>
  )

  return (
    <div className="space-y-4">
      {company.description && <p className="text-sm text-muted-foreground">{company.description}</p>}

      {isRecruiter ? (
        <>
          <RecruiterOverviewSection />
          <InternationalHiringSection />
          <WorkEnvironmentSection />
        </>
      ) : (
        <>
          <OverviewSection />
          <VisaSection />
          <WorkEnvironmentSection />
          <Section title="Engineering Culture" icon={<Briefcase className="w-3 h-3 text-yellow-500" />}>
            <Field label="Organization" value={culture.engineering_org} />
            <Field label="Team Structure" value={culture.team_structure} />
            <Field label="Methodology" value={culture.methodology} />
            <Field label="Tech Decisions" value={culture.tech_decisions} />
            <Field label="Maturity" value={culture.maturity} />
            <Field label="Quality Culture" value={culture.quality_culture} />
            <Field label="Open Source" value={culture.open_source} />
          </Section>
          <Section title="Technology Stack" icon={<Briefcase className="w-3 h-3 text-cyan-500" />}>
            {Array.isArray(tech.backend) && tech.backend.length > 0 && (
              <div className="py-1"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Backend</span><TagList items={tech.backend} /></div>
            )}
            {Array.isArray(tech.frontend) && tech.frontend.length > 0 && (
              <div className="py-1"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Frontend</span><TagList items={tech.frontend} /></div>
            )}
            {Array.isArray(tech.infrastructure) && tech.infrastructure.length > 0 && (
              <div className="py-1"><span className="text-2xs text-muted-foreground uppercase tracking-wide">Infrastructure</span><TagList items={tech.infrastructure} /></div>
            )}
            <Field label="Tech Match Score" value={tech.tech_match_score} />
            <Field label="Matches Profile" value={tech.matches_profile} />
            <Field label="Learning Opportunities" value={tech.learning_opportunities} />
          </Section>
          <Section title="Growth Opportunities" icon={<Briefcase className="w-3 h-3 text-primary" />}>
            <Field label="Senior Opportunities" value={career.senior_opportunities} />
            <Field label="Technical Challenges" value={career.technical_challenges} />
            <Field label="Growth Potential" value={career.growth_potential} />
            <Field label="Learning" value={career.learning_opportunities} />
            <Field label="Career Progression" value={career.career_progression} />
            <Field label="Engineering Impact" value={career.engineering_impact} />
          </Section>
        </>
      )}
    </div>
  )
}

function CompanyScoresSection({ intel }: { intel: CompanyIntelligence | null | undefined }) {
  if (!intel) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <p className="text-sm text-muted-foreground">No scores available yet.</p>
      </div>
    )
  }

  const scores = (intel.scores || {}) as CompanyIntelligenceScores
  const fitScore = typeof scores.company_fit_score === 'number' ? scores.company_fit_score : null
  const successScore = typeof scores.company_success_score === 'number' ? scores.company_success_score : null
  const overallScore = typeof scores.company_overall_score === 'number' ? scores.company_overall_score : null
  const overallGrade = overallScore != null
    ? gradeForScore(overallScore)
    : typeof scores.overall_grade === 'string'
      ? scores.overall_grade
      : typeof scores.fit_grade === 'string'
        ? scores.fit_grade
        : '—'

  const FactorList = ({ title, items, color }: { title: string; items: unknown[]; color: string }) => (
    items.length > 0 ? (
      <div className="mb-2">
        <span className={`text-2xs font-semibold ${color}`}>{title}</span>
        {items.map((f, i) => <p key={i} className={`text-xs mt-0.5 ${color}`}>- {typeof f === 'string' ? f : JSON.stringify(f)}</p>)}
      </div>
    ) : null
  )

  const fitExplanation = typeof scores.fit_explanation === 'string' ? scores.fit_explanation : null
  const successExplanation = typeof scores.success_explanation === 'string' ? scores.success_explanation : null
  const fitPositive = Array.isArray(scores.fit_positive_factors) ? scores.fit_positive_factors as unknown[] : []
  const fitNegative = Array.isArray(scores.fit_negative_factors) ? scores.fit_negative_factors as unknown[] : []
  const successPositive = Array.isArray(scores.success_positive_factors) ? scores.success_positive_factors as unknown[] : []
  const successNegative = Array.isArray(scores.success_negative_factors) ? scores.success_negative_factors as unknown[] : []

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 text-center">
        <div className="text-5xl font-black text-primary mb-1">{overallGrade}</div>
        <div className="text-sm font-semibold text-muted-foreground">Overall Grade</div>
        {overallScore != null && <div className="text-lg font-bold text-primary mt-1">{overallScore}/100</div>}
      </div>

      <div className="rounded-lg border border-border/40 bg-muted/10 p-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex flex-col items-center">
            <div className="text-3xl font-black text-primary">{fitScore ?? '?'}</div>
            <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Fit Score</div>
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold">Company Fit Score</div>
            <div className="text-sm text-muted-foreground">How well does this company match your technical background and career direction?</div>
          </div>
        </div>
        {fitExplanation && <p className="text-sm text-muted-foreground mb-2">{fitExplanation}</p>}
        <FactorList title="Positive Factors" items={fitPositive} color="text-green-500" />
        <FactorList title="Negative Factors" items={fitNegative} color="text-red-400" />
      </div>

      <div className="rounded-lg border border-border/40 bg-muted/10 p-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex flex-col items-center">
            <div className="text-3xl font-black text-primary">{successScore ?? '?'}</div>
            <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Success Score</div>
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold">Company Success Score</div>
            <div className="text-sm text-muted-foreground">How likely are you to successfully join this company?</div>
          </div>
        </div>
        {successExplanation && <p className="text-sm text-muted-foreground mb-2">{successExplanation}</p>}
        <FactorList title="Positive Factors" items={successPositive} color="text-green-500" />
        <FactorList title="Negative Factors" items={successNegative} color="text-red-400" />
      </div>

      {fitScore != null && successScore != null && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-4">
          <div className="text-sm font-semibold mb-2">Score Calculation</div>
          <div className="text-sm text-muted-foreground">
            Overall = Fit ({fitScore}) × 0.5 + Success ({successScore}) × 0.5 = <span className="font-bold text-primary">{overallScore ?? '?'}</span>
          </div>
        </div>
      )}
    </div>
  )
}

function GlobeIcon() {
  return (
    <svg className="w-3 h-3 text-emerald-500" viewBox="0 0 256 256" fill="currentColor">
      <path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm88,104a87.56,87.56,0,0,1-7.11,34.84C199.4,145.05,185,127,159,113.46c8.86-19.65,13.14-39.62,13.54-55.22A88.15,88.15,0,0,1,216,128ZM160.7,31.46c1.34,14.32-3.06,34-11.83,53.78-13.19-5.19-28.4-8.16-44.23-9.17C111.23,50.11,129.57,34.32,160.7,31.46ZM59.63,68.16c3.9,18.42,11.08,38.32,21.48,56.56C64.79,132.73,49.7,143.56,39.53,154.41A87.76,87.76,0,0,1,59.63,68.16ZM128,216c-20.62,0-40-10.2-54.12-26.06,4.5-8.11,13.62-19.48,27.13-28.65,3.07,10.22,7.3,20,12.58,28.35L113.59,189.7c5.16,3.18,10.68,5.88,16.32,8.15C134.38,199.77,138.86,202.08,143.3,204.5c-4.77,7.44-9.88,11.5-15.3,11.5Zm-7.25-35.92c-5.45-8.73-9.78-18.91-12.85-29.59,8.69,2.57,17.66,4.55,26.71,5.82,8.9,1.31,17.78,1.94,26.48,1.94,5.2,0,10.25-.28,15.11-.86-2.84,10.94-6.86,21.22-11.93,30.17-8.53-2.53-18.1-4.37-28.13-5.26C119.05,180.18,112.11,179.97,120.75,180.08Zm30.94,5.91A87.16,87.16,0,0,1,128,216a14.9,14.9,0,0,1-2.43-.2c6.34-3.35,12.27-7.51,17.63-12.29C143.61,203,145.06,201,146.41,198.74ZM190.37,140c-5.12,7.35-13,16.89-23.8,25.93-2.87-10.36-6.91-21-12-30.93a155,155,0,0,0,24.73-22.29A87.66,87.66,0,0,1,190.37,140Z" />
    </svg>
  )
}
