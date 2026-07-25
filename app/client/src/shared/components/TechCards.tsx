import { cn } from '@/shared/lib/utils'
import { Card } from '@/shared/ui/card'
import { Badge } from '@/shared/ui/badge'
import { Separator } from '@/shared/ui/separator'

export function TechCard({ tech }) {
  const pc = {
    p1: 'bg-green-500/15 text-green-500 border-green-500/30',
    p2: 'bg-blue-500/15 text-blue-500 border-blue-500/30',
    p3: 'bg-yellow-500/15 text-yellow-500 border-yellow-500/30',
    p4: 'bg-orange-500/15 text-orange-500 border-orange-500/30',
    p5: 'bg-red-500/15 text-red-500 border-red-500/30'
  }
  const borderColor = tech.pc === 'p1' ? 'border-l-green-500' :
                      tech.pc === 'p2' ? 'border-l-blue-500' :
                      tech.pc === 'p3' ? 'border-l-yellow-500' :
                      tech.pc === 'p4' ? 'border-l-orange-500' : 'border-l-red-500'

  return (
    <Card className={cn("p-3 border-l-[3px] transition hover:border-primary", borderColor)}>
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-sm">{tech.name}</span>
        <Badge variant="outline" className={cn("text-[0.6rem] uppercase border", pc[tech.pc])}>{tech.pl}</Badge>
      </div>
      <div className="flex items-center gap-2 text-xs mb-1.5 text-muted-foreground">
        <span>{tech.usage}%</span>
        <div className="flex-1 h-[3px] rounded-full bg-muted">
          <div className="h-full rounded-full" style={{ width: `${tech.usage}%`, background: tech.uc }} />
        </div>
      </div>
      <div className="text-xs mb-1.5 text-muted-foreground"><b className="text-foreground">{tech.jobs}</b> — {tech.jd}</div>
      <Separator className="my-1.5" />
      <div className="text-xs text-muted-foreground pt-1.5">{tech.reason}</div>
      <Badge variant="secondary" className="text-[0.65rem] mt-2 gap-1">
        <span className={cn("w-1 h-1 rounded-full", tech.dc)} /> {tech.sc} — {tech.action}
      </Badge>
    </Card>
  )
}

export function StackCard({ tech }) {
  const borderColor = tech.mc === 'p1' ? 'border-l-green-500' :
                      tech.mc === 'p2' ? 'border-l-blue-500' :
                      tech.mc === 'p3' ? 'border-l-yellow-500' : 'border-l-red-500'
  const badgeStyle = tech.mc === 'p1' ? 'bg-green-500/15 text-green-500 border-green-500/30' :
                     tech.mc === 'p2' ? 'bg-blue-500/15 text-blue-500 border-blue-500/30' :
                     'bg-yellow-500/15 text-yellow-500 border-yellow-500/30'

  return (
    <Card className={cn("p-3 border-l-[3px] transition hover:border-primary", borderColor)}>
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-sm">{tech.name}</span>
        <Badge variant="outline" className={cn("text-[0.6rem] uppercase border", badgeStyle)}>{tech.ml}</Badge>
      </div>
      <div className="flex gap-0.5 mb-2">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className={cn("flex-1 h-[3px] rounded-full", i < tech.level ? "bg-primary" : "bg-muted")} />
        ))}
      </div>
      <div className="text-xs mb-1 text-muted-foreground"><b className="text-foreground">{tech.roles}</b></div>
      <div className="text-xs text-muted-foreground"><b className="text-primary">Path:</b> {tech.path}</div>
    </Card>
  )
}
