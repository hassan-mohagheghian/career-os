import { useState } from 'react'
import { Buildings, MapPin, ArrowSquareOut, ArrowRight, X, CheckCircle } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'

export default function CompanyTab({ job, companies, onLinkCompany, onSetToast, onOpenCompany, onNavigateToCompany, onClose }) {
  const linkedCompany = job.linked_company || null
  const [search, setSearch] = useState('')
  const [linking, setLinking] = useState(false)
  const [showSelector, setShowSelector] = useState(false)

  const filtered = companies.filter(c => {
    if (!search) return true
    const q = search.toLowerCase()
    return (c.name || '').toLowerCase().includes(q) ||
           (c.industry || '').toLowerCase().includes(q) ||
           (c.city || '').toLowerCase().includes(q)
  })

  const handleLink = async (companyId) => {
    setLinking(true)
    try {
      await onLinkCompany?.(job.num, companyId)
      onSetToast?.('Company linked!')
    } catch (e) {
      onSetToast?.('Failed to link')
    } finally {
      setLinking(false)
    }
  }

  const handleUnlink = async () => {
    setLinking(true)
    try {
      await onLinkCompany?.(job.num, null)
      onSetToast?.('Company unlinked')
    } catch (e) {
      onSetToast?.('Failed to unlink')
    } finally {
      setLinking(false)
    }
  }

  const intel = linkedCompany?.intelligence
  const scores = intel?.scores || linkedCompany?.scores || {}
  const overview = intel?.overview || {}
  const culture = intel?.culture_analysis || {}
  const visa = intel?.visa_analysis || {}
  const tech = intel?.technology_analysis || {}

  const companyFitScore = scores.company_fit_score ?? null
  const companySuccessScore = scores.company_success_score ?? null
  const companyOverallScore = scores.company_overall_score ?? null
  const overallGrade = scores.overall_grade || scores.fit_grade || 'B'

  return (
    <div className="space-y-3">
      {linkedCompany ? (
        <div className="p-3 rounded-lg border border-green-500/30 bg-green-500/5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Buildings className="w-4 h-4 text-green-500" />
              <span className="text-xs font-semibold text-green-500">Linked Company</span>
            </div>
            <div className="flex items-center gap-1">
              {onOpenCompany && (
                <Button variant="ghost" size="icon" className="h-5 w-5 text-primary hover:bg-primary/10" onClick={() => { onClose?.(); onOpenCompany(linkedCompany.id) }} title="Open company drawer">
                  <ArrowSquareOut className="w-3 h-3" />
                </Button>
              )}
              {onNavigateToCompany && (
                <Button variant="ghost" size="icon" className="h-5 w-5 text-muted-foreground hover:bg-muted" onClick={() => { onClose?.(); onNavigateToCompany(linkedCompany.id) }} title="Go to Companies page">
                  <ArrowRight className="w-3 h-3" />
                </Button>
              )}
            </div>
          </div>
          <div className="text-sm font-bold">{linkedCompany.name}</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {linkedCompany.industry && <Badge variant="secondary" className="text-[0.55rem]">{linkedCompany.industry}</Badge>}
            {(linkedCompany.city || linkedCompany.country) && (
              <Badge variant="secondary" className="text-[0.55rem]"><MapPin className="w-2.5 h-2.5 mr-0.5" />{[linkedCompany.city, linkedCompany.country].filter(Boolean).join(', ')}</Badge>
            )}
          </div>

          {intel && (
            <div className="mt-3 pt-3 border-t border-green-500/20">
              <div className="text-[0.55rem] uppercase tracking-wider text-muted-foreground font-semibold mb-2">Company Scores</div>
              <div className="grid grid-cols-4 gap-2 text-center">
                <div>
                  <div className="text-lg font-black text-primary">{overallGrade}</div>
                  <div className="text-[0.5rem] text-muted-foreground">Grade</div>
                </div>
                {companyFitScore !== null && (
                  <div>
                    <div className="text-lg font-bold text-blue-400">{companyFitScore}</div>
                    <div className="text-[0.5rem] text-muted-foreground">Fit</div>
                  </div>
                )}
                {companySuccessScore !== null && (
                  <div>
                    <div className="text-lg font-bold text-emerald-400">{companySuccessScore}</div>
                    <div className="text-[0.5rem] text-muted-foreground">Success</div>
                  </div>
                )}
                {companyOverallScore !== null && (
                  <div>
                    <div className="text-lg font-bold text-purple-400">{companyOverallScore}</div>
                    <div className="text-[0.5rem] text-muted-foreground">Overall</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {intel && (
            <div className="mt-3 pt-3 border-t border-green-500/20">
              <div className="text-[0.55rem] uppercase tracking-wider text-muted-foreground font-semibold mb-2">Intelligence Summary</div>
              <div className="space-y-1.5 text-xs">
                {overview.description && (
                  <p className="text-muted-foreground line-clamp-2">{overview.description}</p>
                )}
                {culture.engineering_org && (
                  <div className="flex gap-1">
                    <span className="text-muted-foreground shrink-0">Culture:</span>
                    <span className="truncate">{culture.engineering_org}</span>
                  </div>
                )}
                {visa.relocation_recommendation && (
                  <div className="flex items-center gap-1">
                    <span className="text-muted-foreground">Relocation:</span>
                    <Badge variant={visa.relocation_recommendation === 'HIGH' ? 'default' : visa.relocation_recommendation === 'MEDIUM' ? 'secondary' : 'outline'}
                      className={cn("text-[0.5rem]",
                        visa.relocation_recommendation === 'HIGH' ? 'bg-emerald-500/15 text-emerald-400' :
                        visa.relocation_recommendation === 'MEDIUM' ? 'bg-yellow-500/15 text-yellow-400' :
                        'bg-red-500/15 text-red-400'
                      )}>
                      {visa.relocation_recommendation}
                    </Badge>
                  </div>
                )}
                {tech.backend && tech.backend.length > 0 && (
                  <div>
                    <span className="text-muted-foreground">Tech: </span>
                    <span className="text-[0.55rem]">{tech.backend.slice(0, 3).join(', ')}{tech.backend.length > 3 ? '...' : ''}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-3 rounded-lg border border-dashed text-center">
          <Buildings className="w-6 h-6 mx-auto mb-1 text-muted-foreground/40" />
          <p className="text-xs text-muted-foreground">No company linked</p>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1 gap-1.5 h-7 text-[0.55rem]"
          onClick={() => setShowSelector(!showSelector)}
        >
          <Buildings className="w-3 h-3" />
          {linkedCompany ? 'Change Company' : 'Link Company'}
        </Button>
        {linkedCompany && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 h-7 text-[0.55rem] text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/30"
            onClick={handleUnlink}
            disabled={linking}
          >
            <X className="w-3 h-3" />
            Disconnect
          </Button>
        )}
      </div>

      {showSelector && (
        <div className="p-3 rounded-lg border border-border/50 bg-muted/30">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search companies..."
            className="w-full h-7 rounded border text-xs px-2 bg-background mb-2"
            autoFocus
          />
          <div className="max-h-48 overflow-y-auto space-y-1">
            {filtered.length === 0 && (
              <div className="text-[0.6rem] text-muted-foreground text-center py-2">No companies found</div>
            )}
            {filtered.map(c => (
              <div key={c.id}
                onClick={() => { if (!linking) { handleLink(c.id); setShowSelector(false) } }}
                className={cn(
                  "flex items-center gap-2 p-1.5 rounded border cursor-pointer transition text-xs",
                  linkedCompany?.id === c.id
                    ? "border-green-500/30 bg-green-500/5"
                    : "border-border/50 hover:bg-muted/50"
                )}>
                {c.logo_url && <img src={c.logo_url} alt="" className="w-4 h-4 rounded" />}
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">{c.name}</div>
                  <div className="text-[0.55rem] text-muted-foreground truncate">{c.industry || ''} {c.city ? `· ${c.city}` : ''}</div>
                </div>
                {linkedCompany?.id === c.id && <CheckCircle className="w-3 h-3 text-green-500 shrink-0" />}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
