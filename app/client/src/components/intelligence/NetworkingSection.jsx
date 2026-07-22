import {
  Users, Gear, IdentificationCard, MagnifyingGlass, Lightbulb,
  CheckCircle, Link, ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function NetworkingSection({ analysis, refreshing, onRefresh }) {
  const networking = analysis.networking || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Networking Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.networking} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.networking && "animate-spin")} /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Networking Targets</h3>
            </div>
            <p className="text-[0.6rem] text-muted-foreground mb-3">Top companies to connect with on LinkedIn.</p>
            <div className="space-y-3">
              {networking.map((item, i) => (
                <div key={i} className="rounded-lg border p-3 space-y-2.5 hover:shadow transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm">{item.company}</span>
                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                        item.score === 'A++' || item.score === 'A+' ? "bg-green-500/15 text-green-500" :
                        item.score === 'A' ? "bg-blue-500/15 text-blue-500" :
                        "bg-yellow-500/15 text-yellow-500"
                      )}>{item.score}</Badge>
                    </div>
                    {item.jobUrl && (
                      <a href={item.jobUrl} target="_blank" rel="noopener noreferrer" className="text-[0.55rem] text-primary hover:underline flex items-center gap-1">
                        <Link className="w-3 h-3" /> View Job
                      </a>
                    )}
                  </div>
                  {item.roles && item.roles.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.roles.map((r, ri) => (
                        <Badge key={ri} variant="outline" className="text-[0.45rem] h-3.5">{r}</Badge>
                      ))}
                    </div>
                  )}
                  <div className="text-[0.6rem] text-muted-foreground">{item.reason}</div>

                  {item.recruiters && item.recruiters.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <IdentificationCard className="w-3 h-3 text-purple-500" />
                        <span className="text-[0.55rem] font-bold text-purple-500">Recruiters</span>
                      </div>
                      {item.recruiters.map((r, ri) => (
                        <a key={ri} href={r.linkedinSearch} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                          {r.title || r.name}
                        </a>
                      ))}
                    </div>
                  )}

                  {item.engineers && item.engineers.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <Gear className="w-3 h-3 text-blue-500" />
                        <span className="text-[0.55rem] font-bold text-blue-500">Engineers</span>
                      </div>
                      {item.engineers.map((e, ei) => (
                        <a key={ei} href={e.linkedinSearch} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                          {e.title || e.name}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {networking.length === 0 && (
                <div className="text-xs text-muted-foreground text-center py-4">
                  Run analysis to generate networking targets.
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-yellow-500" />
              <h3 className="font-extrabold text-sm">Networking Tips</h3>
            </div>
            <div className="space-y-2 text-[0.6rem] text-muted-foreground">
              {[
                'Search for <strong>Recruiters</strong> and <strong>Talent Acquisition</strong> at each company first.',
                'Connect with <strong>Software Engineers</strong> and <strong>Backend Engineers</strong> for referrals.',
                'Personalize your connection request — mention the specific role.',
                'Engage with their posts before connecting.',
                'Follow up 1 week after connecting.',
              ].map((tip, i) => (
                <div key={i} className="flex items-start gap-2">
                  <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                  <span dangerouslySetInnerHTML={{ __html: tip }} />
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Link className="w-5 h-5 text-primary" />
              <h3 className="font-extrabold text-sm">Quick Searches</h3>
            </div>
            <div className="space-y-1.5">
              {[
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22recruiter%22+%22software+engineer%22+Berlin', label: 'Recruiters — Software Engineers Berlin' },
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22talent+acquisition%22+%22backend%22+Berlin', label: 'Talent Acquisition — Backend Berlin' },
                { url: 'https://www.google.com/search?q=site:linkedin.com/in+%22hiring+manager%22+%22python%22+Berlin', label: 'Hiring Managers — Python Berlin' },
              ].map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-[0.6rem] text-primary hover:underline p-1.5 rounded hover:bg-muted transition">
                  <MagnifyingGlass className="w-3 h-3" />
                  {link.label}
                </a>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
