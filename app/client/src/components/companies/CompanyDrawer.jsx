import { useState, useEffect } from 'react'
import {
  Buildings, MapPin, Globe, Users, Repeat, Trash, Link, Lightbulb,
  Shield, Briefcase, Star, Cpu, Rocket, Spinner, Note, Plus, PencilSimple, X, Check
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import ScoreBar from './ScoreBar'
import CompanyJobsTab from './CompanyJobsTab'
import CompanyNotesTab from './CompanyNotesTab'

function Section({ title, icon, children }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
        {icon}{title}
      </div>
      {children}
    </div>
  )
}

function Field({ label, value }) {
  if (!value) return null
  return (
    <div className="flex gap-2">
      <span className="text-xs text-muted-foreground shrink-0">{label}:</span>
      <span className="text-xs">{value}</span>
    </div>
  )
}

function TagList({ items }) {
  if (!items || !items.length) return null
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((item, i) => (
        <span key={i} className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-secondary text-secondary-foreground">
          {item}
        </span>
      ))}
    </div>
  )
}

export default function CompanyDrawer({ company, onClose, onDelete, onReprocess }) {
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

  return (
    <Sheet open={!!company} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[min(640px,92vw)] sm:max-w-[640px] overflow-y-auto p-4 pr-12">
        <SheetHeader className="mb-4">
          <div className="flex gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <div className="flex flex-col items-center">
                  <div className="text-4xl font-black text-primary">{scores.priority || 'B'}</div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Priority</div>
                </div>
                <div className="flex flex-col items-center">
                  <div className="text-lg font-bold text-emerald-400">{scores.visa_score ?? '?'}</div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Visa</div>
                </div>
                <div className="flex flex-col items-center">
                  <div className="text-lg font-bold text-blue-400">{scores.tech_match ?? '?'}</div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Tech</div>
                </div>
                <div className="flex flex-col items-center">
                  <div className="text-lg font-bold text-purple-400">{scores.career_score ?? '?'}</div>
                  <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">Career</div>
                </div>
              </div>
              <SheetTitle className="text-lg">{company.name}</SheetTitle>
              <SheetDescription>{company.industry || 'Technology'}</SheetDescription>
              <div className="flex flex-wrap gap-1 mt-2">
                {(company.city || company.country) && (
                  <Badge variant="secondary" className="text-[0.55rem]"><MapPin className="w-2.5 h-2.5 mr-1" />{[company.city, company.country].filter(Boolean).join(', ')}</Badge>
                )}
                {company.company_size && <Badge variant="secondary" className="text-[0.55rem]"><Users className="w-2.5 h-2.5 mr-1" />{company.company_size}</Badge>}
                {company.company_type && <Badge variant="secondary" className="text-[0.55rem]">{company.company_type}</Badge>}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              {company.website && (
                <a href={company.website} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm" className="gap-1 h-7 text-[0.6rem]"><Link className="w-3 h-3" /> Website</Button>
                </a>
              )}
              {onReprocess && (
                <Button variant="ghost" size="sm" className="gap-1 h-7 text-[0.6rem]" onClick={() => onReprocess(company.id)}>
                  <Repeat className="w-3 h-3" /> Reprocess
                </Button>
              )}
              {onDelete && (
                <Button variant="ghost" size="sm" className="gap-1 h-7 text-[0.6rem] text-destructive" onClick={() => onDelete(company.id)}>
                  <Trash className="w-3 h-3" /> Delete
                </Button>
              )}
            </div>
          </div>
        </SheetHeader>

        {!intel && (
          <Card className="p-6 text-center border-dashed">
            <Buildings className="w-8 h-8 mx-auto mb-2 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">No intelligence data yet. Processing may be in progress.</p>
          </Card>
        )}

        {intel && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="bg-muted w-full justify-start flex-wrap h-auto gap-1 p-1">
              <TabsTrigger value="overview" className="text-[0.6rem] gap-1"><Buildings className="w-3 h-3" />Overview</TabsTrigger>
              <TabsTrigger value="culture" className="text-[0.6rem] gap-1"><Lightbulb className="w-3 h-3" />Culture</TabsTrigger>
              <TabsTrigger value="international" className="text-[0.6rem] gap-1"><Globe className="w-3 h-3" />International</TabsTrigger>
              <TabsTrigger value="career" className="text-[0.6rem] gap-1"><Briefcase className="w-3 h-3" />Career</TabsTrigger>
              <TabsTrigger value="benefits" className="text-[0.6rem] gap-1"><Star className="w-3 h-3" />Benefits</TabsTrigger>
              <TabsTrigger value="visa" className="text-[0.6rem] gap-1"><Shield className="w-3 h-3" />Visa</TabsTrigger>
              <TabsTrigger value="tech" className="text-[0.6rem] gap-1"><Cpu className="w-3 h-3" />Tech</TabsTrigger>
              <TabsTrigger value="recommendation" className="text-[0.6rem] gap-1"><Rocket className="w-3 h-3" />Recommendation</TabsTrigger>
              <TabsTrigger value="jobs" className="text-[0.6rem] gap-1"><Briefcase className="w-3 h-3" />Jobs</TabsTrigger>
              <TabsTrigger value="notes" className="text-[0.6rem] gap-1"><Note className="w-3 h-3" />Notes</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="mt-3 space-y-3">
              <Section title="Overview" icon={<Buildings className="w-4 h-4 text-primary" />}>
                {company.description && <p className="text-xs text-muted-foreground">{company.description}</p>}
                <Field label="Products" value={overview.products} />
                <Field label="Founded" value={overview.founded} />
                <Field label="Headquarters" value={overview.headquarters} />
                <Field label="Size" value={overview.size || company.company_size} />
                {overview.countries && overview.countries.length > 0 && (
                  <div>
                    <span className="text-xs text-muted-foreground">Countries:</span>
                    <TagList items={overview.countries} />
                  </div>
                )}
              </Section>
            </TabsContent>

            {/* Culture Tab */}
            <TabsContent value="culture" className="mt-3 space-y-3">
              <Section title="Engineering Culture" icon={<Lightbulb className="w-4 h-4 text-yellow-400" />}>
                <Field label="Organization" value={culture.engineering_org} />
                <Field label="Team Structure" value={culture.team_structure} />
                <Field label="Methodology" value={culture.methodology} />
                <Field label="Tech Decisions" value={culture.tech_decisions} />
                <Field label="Maturity" value={culture.maturity} />
                <Field label="Environment" value={culture.environment} />
                <Field label="Quality Culture" value={culture.quality_culture} />
                <Field label="Open Source" value={culture.open_source} />
              </Section>
            </TabsContent>

            {/* International Tab */}
            <TabsContent value="international" className="mt-3 space-y-3">
              <Section title="International Environment" icon={<Globe className="w-4 h-4 text-blue-400" />}>
                <ScoreBar label="International" value={international.international_score} />
                <Field label="English Usage" value={international.english_usage} />
                <Field label="International Employees" value={international.international_employees} />
                <Field label="Global Teams" value={international.global_teams} />
                <Field label="Remote Collaboration" value={international.remote_collaboration} />
                <Field label="Diversity" value={international.diversity} />
              </Section>
            </TabsContent>

            {/* Career Tab */}
            <TabsContent value="career" className="mt-3 space-y-3">
              <Section title="Career Opportunity" icon={<Briefcase className="w-4 h-4 text-green-400" />}>
                <ScoreBar label="Career Score" value={career.career_score} />
                <Field label="Senior Opportunities" value={career.senior_opportunities} />
                <Field label="Technical Challenges" value={career.technical_challenges} />
                <Field label="Growth Potential" value={career.growth_potential} />
                <Field label="Learning" value={career.learning_opportunities} />
                <Field label="Progression" value={career.career_progression} />
                <Field label="Impact" value={career.engineering_impact} />
              </Section>
            </TabsContent>

            {/* Benefits Tab */}
            <TabsContent value="benefits" className="mt-3 space-y-3">
              <Section title="Benefits & Work Environment" icon={<Star className="w-4 h-4 text-purple-400" />}>
                <Field label="Salary" value={benefits.salary_info} />
                <Field label="Remote Policy" value={benefits.remote_policy} />
                <Field label="Hybrid Policy" value={benefits.hybrid_policy} />
                <Field label="Vacation" value={benefits.vacation} />
                <Field label="Learning Budget" value={benefits.learning_budget} />
                <Field label="Equipment" value={benefits.equipment} />
                <Field label="Relocation" value={benefits.relocation} />
                {benefits.benefits && benefits.benefits.length > 0 && (
                  <div>
                    <span className="text-xs text-muted-foreground">Benefits:</span>
                    <TagList items={benefits.benefits} />
                  </div>
                )}
              </Section>
            </TabsContent>

            {/* Visa Tab */}
            <TabsContent value="visa" className="mt-3 space-y-3">
              <Section title="Relocation Intelligence" icon={<Shield className="w-4 h-4 text-emerald-400" />}>
                <ScoreBar label="Visa Score" value={visa.visa_score} />
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">Relocation:</span>
                  <Badge variant={visa.relocation_recommendation === 'HIGH' ? 'default' : visa.relocation_recommendation === 'MEDIUM' ? 'secondary' : 'outline'}
                    className={cn("text-[0.55rem]",
                      visa.relocation_recommendation === 'HIGH' ? 'bg-emerald-500/15 text-emerald-400' :
                      visa.relocation_recommendation === 'MEDIUM' ? 'bg-yellow-500/15 text-yellow-400' :
                      'bg-red-500/15 text-red-400'
                    )}>
                    {visa.relocation_recommendation || 'Uncertain'}
                  </Badge>
                </div>
                <Field label="Sponsorship History" value={visa.sponsorship_history} />
                <Field label="International Hiring" value={visa.international_hiring} />
                <Field label="Relocation Programs" value={visa.relocation_programs} />
                <Field label="English First" value={visa.english_first} />
                <Field label="Country Restrictions" value={visa.country_restrictions} />
                {visa.positive_signals && visa.positive_signals.length > 0 && (
                  <div>
                    <span className="text-xs text-green-500 font-semibold">Positive Signals:</span>
                    {visa.positive_signals.map((s, i) => <p key={i} className="text-xs mt-0.5">- {s}</p>)}
                  </div>
                )}
                {visa.risks && visa.risks.length > 0 && (
                  <div>
                    <span className="text-xs text-red-400 font-semibold">Risks:</span>
                    {visa.risks.map((r, i) => <p key={i} className="text-xs mt-0.5">- {r}</p>)}
                  </div>
                )}
                <Field label="Recommended Approach" value={visa.recommended_approach} />
              </Section>
            </TabsContent>

            {/* Tech Tab */}
            <TabsContent value="tech" className="mt-3 space-y-3">
              <Section title="Technology Intelligence" icon={<Cpu className="w-4 h-4 text-cyan-400" />}>
                <ScoreBar label="Tech Match" value={tech.tech_match_score} />
                {tech.backend && tech.backend.length > 0 && (
                  <div><span className="text-xs text-muted-foreground">Backend:</span><TagList items={tech.backend} /></div>
                )}
                {tech.frontend && tech.frontend.length > 0 && (
                  <div><span className="text-xs text-muted-foreground">Frontend:</span><TagList items={tech.frontend} /></div>
                )}
                {tech.infrastructure && tech.infrastructure.length > 0 && (
                  <div><span className="text-xs text-muted-foreground">Infrastructure:</span><TagList items={tech.infrastructure} /></div>
                )}
                {tech.data && tech.data.length > 0 && (
                  <div><span className="text-xs text-muted-foreground">Data:</span><TagList items={tech.data} /></div>
                )}
                <Field label="Matches Profile" value={tech.matches_profile} />
                <Field label="Missing Technologies" value={tech.missing_tech} />
                <Field label="Learning Opportunities" value={tech.learning_opportunities} />
              </Section>
            </TabsContent>

            {/* Recommendation Tab */}
            <TabsContent value="recommendation" className="mt-3 space-y-3">
              <Section title="AI Recommendation" icon={<Rocket className="w-4 h-4 text-orange-400" />}>
                {recommendation.priority && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-muted-foreground">Priority:</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-sm font-black"
                      style={{
                        background: ['A++','A+'].includes(recommendation.priority) ? 'rgba(16,185,129,0.2)' : recommendation.priority === 'A' ? 'rgba(34,197,94,0.12)' : 'rgba(59,130,246,0.12)',
                        color: ['A++','A+'].includes(recommendation.priority) ? '#10b981' : recommendation.priority === 'A' ? '#22c55e' : '#3b82f6'
                      }}>
                      {recommendation.priority}
                    </span>
                  </div>
                )}
                <Card className="p-3 space-y-2 bg-muted/50">
                  <Field label="Observation" value={recommendation.observation} />
                  <Field label="Evidence" value={recommendation.evidence} />
                  <Field label="Impact" value={recommendation.impact} />
                  <Field label="Action" value={recommendation.action} />
                </Card>
              </Section>
            </TabsContent>

            {/* Jobs Tab */}
            <TabsContent value="jobs" className="mt-3">
              <CompanyJobsTab companyId={company.id} />
            </TabsContent>

            {/* Notes Tab */}
            <TabsContent value="notes" className="mt-3">
              <CompanyNotesTab company={company} />
            </TabsContent>
          </Tabs>
        )}
      </SheetContent>
    </Sheet>
  )
}
