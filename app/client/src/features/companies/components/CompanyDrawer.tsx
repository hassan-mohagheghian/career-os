import { useState } from 'react'
import {
  Buildings, MapPin, Globe, Users, Repeat, Trash, Link, Lightbulb,
  Shield, Briefcase, Star, Cpu, Rocket, Spinner, Note, Plus, PencilSimple, X, Check, TrendUp, TrendDown, Clock, CaretDown, CaretRight
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/shared/ui/tabs'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/shared/ui/collapsible'
import { AppDrawer, Section, Field, TagList } from '@/shared/components/DrawerComponents'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import { useLocalHistory } from '@/shared/hooks'
import { STEP_CONFIGS } from '@/shared/components/GenerationProgressCard'
import ScoreBar from './ScoreBar'
import CompanyJobsTab from './CompanyJobsTab'
import CompanyNotesTab from './CompanyNotesTab'

const COMPANY_TYPE_LABELS = {
  PRODUCT_COMPANY: 'Product Company',
  RECRUITING_AGENCY: 'Recruiting Agency',
  STAFFING_COMPANY: 'Staffing Company',
  CONSULTING_COMPANY: 'Consulting Company',
  UNKNOWN: 'Unknown',
}

function formatCompanyType(type) {
  return COMPANY_TYPE_LABELS[type] || type || 'Unknown'
}

function isRecruiterType(type) {
  return type === 'RECRUITING_AGENCY' || type === 'STAFFING_COMPANY'
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  const bg = value >= 80 ? 'bg-emerald-500/15 text-emerald-400' :
    value >= 60 ? 'bg-blue-500/15 text-blue-400' :
    value >= 40 ? 'bg-yellow-500/15 text-yellow-400' :
    'bg-red-500/15 text-red-400'
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground flex-1">{label}</span>
      <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-bold", bg)}>{value}</span>
    </div>
  )
}

export default function CompanyDrawer({ company, onClose, onDelete, onReprocess, onOpenJob, onNavigateToJob, onViewAllJobs }) {
  const [activeTab, setActiveTab] = useState('notes')
  const [showProcessing, setShowProcessing] = useState(false)
  const { items: companyHistory, singleRunning } = useLocalHistory({
    context: 'company',
    company_id: company?.id,
    enabled: !!company?.id,
  })

  if (!company) return null

  const intel = company.intelligence
  const scores = intel?.scores || company.scores || {}
  const overview = intel?.overview || {}
  const culture = intel?.culture_analysis || {}
  const international = intel?.international_analysis || {}
  const career = intel?.career_analysis || {}
  const benefits = intel?.benefits_analysis || {}
  const visa = intel?.visa_analysis || {}
  const tech = intel?.technology_analysis || {}
  const recommendation = intel?.recommendation || {}

  const fitScore = scores.company_fit_score ?? null
  const successScore = scores.company_success_score ?? null
  const overallScore = scores.company_overall_score ?? null
  const overallGrade = scores.overall_grade || scores.fit_grade || '—'

  return (
    <AppDrawer open={!!company} onOpenChange={(open) => !open && onClose()}>
      <div className="p-6 pb-3">
          <div className="flex gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <div className="flex flex-col items-center">
                  <div className="text-4xl font-black text-primary">{overallGrade}</div>
                  <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Grade</div>
                </div>
                {fitScore != null && (
                  <div className="flex flex-col items-center">
                    <div className="text-lg font-bold text-primary">{fitScore}</div>
                    <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Fit</div>
                  </div>
                )}
                {successScore != null && (
                  <div className="flex flex-col items-center">
                    <div className="text-lg font-bold text-primary">{successScore}</div>
                    <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Success</div>
                  </div>
                )}
                {overallScore != null && (
                  <div className="flex flex-col items-center">
                    <div className="text-lg font-bold text-primary">{overallScore}</div>
                    <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Overall</div>
                  </div>
                )}
              </div>
              <div className="text-lg font-semibold">{company.name}</div>
              <div className="text-sm text-muted-foreground">{company.industry || 'Technology'}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {(company.city || company.country) && (
                  <Badge variant="secondary" className="text-2xs"><MapPin className="w-2.5 h-2.5 mr-1" />{[company.city, company.country].filter(Boolean).join(', ')}</Badge>
                )}
                {company.company_size && <Badge variant="secondary" className="text-2xs"><Users className="w-2.5 h-2.5 mr-1" />{company.company_size}</Badge>}
                {company.company_type && <Badge variant="secondary" className="text-2xs">{formatCompanyType(company.company_type)}</Badge>}
                {company.job_count > 0 && (
                  <Badge variant="secondary" className="text-2xs bg-primary/10 text-primary">
                    <Briefcase className="w-2.5 h-2.5 mr-1" />{company.job_count} job{company.job_count !== 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              {company.job_count > 0 && onViewAllJobs && (
                <Button variant="outline" size="sm" className="gap-1 h-7 text-2xs" onClick={() => onViewAllJobs(company.name)}>
                  <Briefcase className="w-3 h-3" /> View All Jobs
                </Button>
              )}
              {company.website && (
                <a href={company.website} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm" className="gap-1 h-7 text-2xs"><Link className="w-3 h-3" /> Website</Button>
                </a>
              )}
              {onReprocess && (
                <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs" onClick={() => onReprocess(company.id)}>
                  <Repeat className="w-3 h-3" /> Reprocess
                </Button>
              )}
              {onDelete && (
                <Button variant="ghost" size="sm" className="gap-1 h-7 text-2xs text-destructive" onClick={() => onDelete(company.id)}>
                  <Trash className="w-3 h-3" /> Delete
                </Button>
              )}
            </div>
          </div>

        {/* Processing History - Collapsible */}
        {companyHistory.length > 0 && (
          <Collapsible open={showProcessing} onOpenChange={setShowProcessing}>
            <div className="mb-3">
              <CollapsibleTrigger asChild>
                <button className="flex items-center gap-1.5 text-2xs font-semibold text-muted-foreground hover:text-foreground transition w-full text-left">
                  {showProcessing ? <CaretDown className="w-3 h-3" /> : <CaretRight className="w-3 h-3" />}
                  <Clock className="w-3 h-3" />
                  Processing History
                  <Badge variant="secondary" className="ml-auto text-2xs h-4">{companyHistory.length}</Badge>
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-1.5 space-y-0.5 pl-1">
                {companyHistory.map(h => (
                  <GenerationHistoryItem key={`${h.source}-${h.id}`} item={h} compact />
                ))}
              </CollapsibleContent>
            </div>
          </Collapsible>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-3">
          <TabsList className="bg-muted">
            <TabsTrigger value="notes">Original Notes</TabsTrigger>
            <TabsTrigger value="intelligence">Intelligence</TabsTrigger>
            <TabsTrigger value="scores">Scores</TabsTrigger>
            <TabsTrigger value="jobs">Jobs{company.job_count > 0 && ` (${company.job_count})`}</TabsTrigger>
          </TabsList>

          {/* Tab 1: Original Notes */}
          <TabsContent value="notes" className="mt-3">
            <CompanyNotesTab company={company} />
          </TabsContent>

          {/* Tab 2: Company Intelligence */}
          <TabsContent value="intelligence" className="mt-3 space-y-4">
            {/* Running progress */}
            {singleRunning && (
              <GenerationProgressCard
                title={singleRunning.title}
                type={singleRunning.source}
                progress={{ running: true, status: singleRunning.status, step: (singleRunning as any).step }}
                steps={STEP_CONFIGS[singleRunning.source]?.steps || STEP_CONFIGS['company-processing'].steps}
              />
            )}

            {!intel && (
              <Card className="p-6 text-center border-dashed">
                <Buildings className="w-8 h-8 mx-auto mb-2 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">No intelligence data yet. Processing may be in progress.</p>
              </Card>
            )}

            {intel && isRecruiterType(company.company_type) ? (
              <>
                {/* Recruiter Overview */}
                <Section title="Recruiter Overview" icon={<Buildings className="w-4 h-4 text-primary" />}>
                  {company.description && <p className="text-sm text-muted-foreground">{company.description}</p>}
                  <Field label="Founded" value={overview.founded} />
                  <Field label="Headquarters" value={overview.headquarters} />
                  <Field label="Size" value={overview.size || company.company_size} />
                  {overview.countries && overview.countries.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Countries:</span>
                      <TagList items={overview.countries} />
                    </div>
                  )}
                </Section>

                {/* Recruitment Specialization */}
                <Section title="Recruitment Specialization" icon={<Briefcase className="w-4 h-4 text-orange-400" />}>
                  <Field label="Market Position" value={overview.market_position} />
                  <Field label="Funding Summary" value={overview.funding_summary} />
                  <Field label="Growth Trajectory" value={overview.growth_trajectory} />
                </Section>

                {/* International Hiring */}
                <Section title="International Hiring" icon={<Globe className="w-4 h-4 text-emerald-400" />}>
                  <Field label="English Usage" value={international.english_usage} />
                  <Field label="International Employees" value={international.international_employees} />
                  <Field label="Visa Sponsorship" value={visa.sponsorship_history} />
                  <Field label="International Hiring" value={visa.international_hiring} />
                  {visa.positive_signals && visa.positive_signals.length > 0 && (
                    <div>
                      <span className="text-sm text-green-500 font-semibold">Positive Signals:</span>
                      {visa.positive_signals.map((s, i) => <p key={i} className="text-sm mt-0.5">- {s}</p>)}
                    </div>
                  )}
                </Section>

                {/* Work Environment */}
                <Section title="Work Environment" icon={<Briefcase className="w-4 h-4 text-green-400" />}>
                  <Field label="Remote Policy" value={benefits.remote_policy} />
                  <Field label="Vacation" value={benefits.vacation} />
                  {benefits.benefits && benefits.benefits.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Benefits:</span>
                      <TagList items={benefits.benefits} />
                    </div>
                  )}
                </Section>
              </>
            ) : intel && (
              <>
                {/* Product Company Sections */}
                {/* Company Overview */}
                <Section title="Company Overview" icon={<Buildings className="w-4 h-4 text-primary" />}>
                  {company.description && <p className="text-sm text-muted-foreground">{company.description}</p>}
                  <Field label="Products" value={overview.products} />
                  <Field label="Founded" value={overview.founded} />
                  <Field label="Headquarters" value={overview.headquarters} />
                  <Field label="Size" value={overview.size || company.company_size} />
                  {overview.countries && overview.countries.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Countries:</span>
                      <TagList items={overview.countries} />
                    </div>
                  )}
                </Section>

                {/* Product & Business */}
                <Section title="Product & Business" icon={<Rocket className="w-4 h-4 text-orange-400" />}>
                  <Field label="Market Position" value={overview.market_position} />
                  <Field label="Funding Summary" value={overview.funding_summary} />
                  <Field label="Growth Trajectory" value={overview.growth_trajectory} />
                </Section>

                {/* Engineering Culture */}
                <Section title="Engineering Culture" icon={<Lightbulb className="w-4 h-4 text-yellow-400" />}>
                  <Field label="Organization" value={culture.engineering_org} />
                  <Field label="Team Structure" value={culture.team_structure} />
                  <Field label="Methodology" value={culture.methodology} />
                  <Field label="Tech Decisions" value={culture.tech_decisions} />
                  <Field label="Maturity" value={culture.maturity} />
                  <Field label="Quality Culture" value={culture.quality_culture} />
                  <Field label="Open Source" value={culture.open_source} />
                </Section>

                {/* Technology Stack */}
                <Section title="Technology Stack" icon={<Cpu className="w-4 h-4 text-cyan-400" />}>
                  {tech.backend && tech.backend.length > 0 && (
                    <div><span className="text-sm text-muted-foreground">Backend:</span><TagList items={tech.backend} /></div>
                  )}
                  {tech.frontend && tech.frontend.length > 0 && (
                    <div><span className="text-sm text-muted-foreground">Frontend:</span><TagList items={tech.frontend} /></div>
                  )}
                  {tech.infrastructure && tech.infrastructure.length > 0 && (
                    <div><span className="text-sm text-muted-foreground">Infrastructure:</span><TagList items={tech.infrastructure} /></div>
                  )}
                  <Field label="Tech Match Score" value={tech.tech_match_score} />
                  <Field label="Matches Profile" value={tech.matches_profile} />
                  <Field label="Learning Opportunities" value={tech.learning_opportunities} />
                </Section>

                {/* Work Environment */}
                <Section title="Work Environment" icon={<Briefcase className="w-4 h-4 text-green-400" />}>
                  <Field label="Remote Policy" value={benefits.remote_policy} />
                  <Field label="Hybrid Policy" value={benefits.hybrid_details || benefits.hybrid_policy} />
                  <Field label="Vacation" value={benefits.vacation} />
                  <Field label="Learning Budget" value={benefits.learning_budget} />
                  <Field label="Equipment" value={benefits.equipment} />
                  {benefits.benefits && benefits.benefits.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Benefits:</span>
                      <TagList items={benefits.benefits} />
                    </div>
                  )}
                </Section>

                {/* Visa & Relocation Signals */}
                <Section title="Visa & Relocation Signals" icon={<Shield className="w-4 h-4 text-emerald-400" />}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm text-muted-foreground">Relocation:</span>
                    <Badge variant={visa.relocation_recommendation === 'HIGH' ? 'default' : visa.relocation_recommendation === 'MEDIUM' ? 'secondary' : 'outline'}
                      className={cn("text-xs",
                        visa.relocation_recommendation === 'HIGH' ? 'bg-emerald-500/15 text-emerald-400' :
                        visa.relocation_recommendation === 'MEDIUM' ? 'bg-yellow-500/15 text-yellow-400' :
                        'bg-red-500/15 text-red-400'
                      )}>
                      {visa.relocation_recommendation || 'Uncertain'}
                    </Badge>
                  </div>
                  <Field label="Sponsorship History" value={visa.sponsorship_history} />
                  <Field label="International Hiring" value={visa.international_hiring} />
                  <Field label="English First" value={visa.english_first} />
                  {visa.positive_signals && visa.positive_signals.length > 0 && (
                    <div>
                      <span className="text-sm text-green-500 font-semibold">Positive Signals:</span>
                      {visa.positive_signals.map((s, i) => <p key={i} className="text-sm mt-0.5">- {s}</p>)}
                    </div>
                  )}
                  {visa.risks && visa.risks.length > 0 && (
                    <div>
                      <span className="text-sm text-red-400 font-semibold">Risks:</span>
                      {visa.risks.map((r, i) => <p key={i} className="text-sm mt-0.5">- {r}</p>)}
                    </div>
                  )}
                </Section>

                {/* Growth Opportunities */}
                <Section title="Growth Opportunities" icon={<TrendUp className="w-4 h-4 text-primary" />}>
                  <Field label="Senior Opportunities" value={career.senior_opportunities} />
                  <Field label="Technical Challenges" value={career.technical_challenges} />
                  <Field label="Growth Potential" value={career.growth_potential} />
                  <Field label="Learning" value={career.learning_opportunities} />
                  <Field label="Career Progression" value={career.career_progression} />
                  <Field label="Engineering Impact" value={career.engineering_impact} />
                </Section>

                {/* Risks and Concerns */}
                {(visa.risks && visa.risks.length > 0) || (tech.missing_tech) ? (
                  <Section title="Risks & Concerns" icon={<Shield className="w-4 h-4 text-red-400" />}>
                    {visa.risks && visa.risks.map((r, i) => <p key={i} className="text-sm text-red-400 mt-0.5">- {r}</p>)}
                    <Field label="Missing Technologies" value={tech.missing_tech} />
                  </Section>
                ) : null}
              </>
            )}
          </TabsContent>
          <TabsContent value="scores" className="mt-3 space-y-4">
            {!intel && (
              <Card className="p-6 text-center border-dashed">
                <TrendUp className="w-8 h-8 mx-auto mb-2 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">No scores available yet.</p>
              </Card>
            )}

            {intel && (
              <>
                {/* Overall Grade */}
                <Card className="p-4 bg-primary/5 border-primary/20">
                  <div className="text-center">
                    <div className="text-5xl font-black text-primary mb-1">{overallGrade}</div>
                    <div className="text-sm font-semibold text-muted-foreground">Overall Grade</div>
                    {overallScore != null && (
                      <div className="text-lg font-bold text-primary mt-1">{overallScore}/100</div>
                    )}
                  </div>
                </Card>

                {/* Fit Score */}
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex flex-col items-center">
                      <div className="text-3xl font-black text-primary">{fitScore ?? '?'}</div>
                      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Fit Score</div>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-semibold">Company Fit Score</div>
                      <div className="text-sm text-muted-foreground">
                        How well does this company match your technical background and career direction?
                      </div>
                    </div>
                  </div>
                  {scores.fit_explanation && (
                    <p className="text-sm text-muted-foreground mb-2">{scores.fit_explanation}</p>
                  )}
                  {scores.fit_positive_factors && scores.fit_positive_factors.length > 0 && (
                    <div className="mb-2">
                      <span className="text-sm text-green-500 font-semibold">Positive Factors:</span>
                      {scores.fit_positive_factors.map((f: string, i: number) => <p key={i} className="text-sm text-green-400 mt-0.5">+ {f}</p>)}
                    </div>
                  )}
                  {scores.fit_negative_factors && scores.fit_negative_factors.length > 0 && (
                    <div>
                      <span className="text-sm text-red-400 font-semibold">Negative Factors:</span>
                      {scores.fit_negative_factors.map((f: string, i: number) => <p key={i} className="text-sm text-red-400 mt-0.5">- {f}</p>)}
                    </div>
                  )}
                </Card>

                {/* Success Score */}
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex flex-col items-center">
                      <div className="text-3xl font-black text-primary">{successScore ?? '?'}</div>
                      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">Success Score</div>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-semibold">Company Success Score</div>
                      <div className="text-sm text-muted-foreground">
                        How likely are you to successfully join this company?
                      </div>
                    </div>
                  </div>
                  {scores.success_explanation && (
                    <p className="text-sm text-muted-foreground mb-2">{scores.success_explanation}</p>
                  )}
                  {scores.success_positive_factors && scores.success_positive_factors.length > 0 && (
                    <div className="mb-2">
                      <span className="text-sm text-green-500 font-semibold">Positive Factors:</span>
                      {scores.success_positive_factors.map((f: string, i: number) => <p key={i} className="text-sm text-green-400 mt-0.5">+ {f}</p>)}
                    </div>
                  )}
                  {scores.success_negative_factors && scores.success_negative_factors.length > 0 && (
                    <div>
                      <span className="text-sm text-red-400 font-semibold">Negative Factors:</span>
                      {scores.success_negative_factors.map((f: string, i: number) => <p key={i} className="text-sm text-red-400 mt-0.5">- {f}</p>)}
                    </div>
                  )}
                </Card>

                {/* Overall Calculation */}
                {fitScore != null && successScore != null && (
                  <Card className="p-4">
                    <div className="text-sm font-semibold mb-2">Score Calculation</div>
                    <div className="text-sm text-muted-foreground">
                      Overall = Fit ({fitScore}) × 0.5 + Success ({successScore}) × 0.5 = <span className="font-bold text-primary">{overallScore ?? '?'}</span>
                    </div>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          {/* Tab 4: Jobs */}
          <TabsContent value="jobs" className="mt-3">
            <CompanyJobsTab companyId={company.id} onOpenJob={onOpenJob} onNavigateToJob={onNavigateToJob} />
          </TabsContent>
        </Tabs>
      </div>
    </AppDrawer>
  )
}
