import { useEffect, useRef } from 'react'
import { Check, Spinner, Confetti } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Badge } from '@/shared/ui/badge'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'

export default function WorkflowTerminal({ workflowDrawer, workflowLogs, workflowEndRef, onClose }) {
  useEffect(() => { workflowEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [workflowLogs])

  return (
    <Sheet open={!!workflowDrawer} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[min(600px,92vw)] sm:max-w-[600px] flex flex-col p-0">
        <SheetHeader className="px-4 py-2.5 border-b">
          <div className="flex items-center gap-2">
            <span className="text-sm">💻</span>
            <SheetTitle className="text-sm">Workflow Terminal</SheetTitle>
            <Badge variant="secondary" className="text-[0.6rem]">{workflowDrawer?.company || 'Job'} #{workflowDrawer?.job_num || '?'}</Badge>
            {workflowDrawer?.status === 'processing' && (
              <Badge variant="default" className="text-[0.55rem] animate-pulse">● LIVE</Badge>
            )}
          </div>
        </SheetHeader>

        {/* Step progress */}
        <div className="px-4 py-2 flex gap-1 border-b bg-muted overflow-x-auto">
          {['fetch', 'validate', 'extract_raw', 'extract_struct', 'summary', 'save', 'analyze', 'done'].map((s, i) => {
            const stepDbCol = { save: 'step_resume', analyze: 'step_analyze' }[s] || `step_${s}`
            const stepVal = workflowDrawer?.[stepDbCol]
            const isDone = stepVal === 1
            const isActive = !isDone && workflowLogs.some(l => l.step === s)
            return (
              <div key={s} className="flex items-center gap-0.5 shrink-0">
                <div className={cn(
                  "w-4 h-4 rounded-full flex items-center justify-center text-[0.45rem] font-bold transition-all border",
                  isDone ? "bg-green-500 text-white border-green-500" :
                  isActive ? "bg-primary text-primary-foreground border-primary" :
                  "bg-background text-muted-foreground border-border"
                )}>
                  {isDone ? <Check className="w-2.5 h-2.5" /> : isActive ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : i + 1}
                </div>
                {i < 7 && <div className={cn("h-[1px] w-3 rounded-full", isDone ? "bg-green-500" : "bg-border")} />}
              </div>
            )
          })}
        </div>

        {/* Terminal output */}
        <ScrollArea ref={workflowEndRef} className="flex-1 font-mono text-[0.7rem] leading-relaxed bg-[#0d1117] text-[#c9d1d9]">
          <div className="p-3">
            {workflowLogs.length === 0 && (
              <div className="text-center py-12 text-[#484f58]">
                <Spinner className="w-8 h-8 animate-spin mx-auto mb-2" />
                <div>Waiting for workflow output...</div>
                <div className="text-[0.6rem] mt-1 text-[#21262d]">WebSocket connecting to stream server...</div>
              </div>
            )}
            {workflowLogs.map((log, i) => {
              const isCmd = log.step === 'cmd'; const isOut = log.step === 'out'; const isErr = log.step === 'err'
              const isMimo = log.step === 'mimo'; const isStep = log.step === 'step'; const isError = log.step === 'error'; const isDone = log.step === 'done'
              return (
                <div key={i} className={cn("mb-0.5", isError || isErr ? "bg-red-500/10 -mx-3 px-3 py-0.5 rounded" : "")}>
                  {isCmd ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#58a6ff]">$</span><span className="text-[#58a6ff]">{log.msg}</span></div> :
                   isOut ? <div className="pl-[70px] text-[#8b949e]">{log.msg}</div> :
                   isErr ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#f85149]">✗</span><span className="text-[#f85149]">{log.msg}</span></div> :
                   <div className="flex gap-2">
                     <span className="text-[#484f58] shrink-0">{log.ts}</span>
                     {!isMimo && !isStep && <span className="font-bold uppercase shrink-0 text-[#58a6ff]" style={{ minWidth: '50px' }}>[{log.step}]</span>}
                     <span className={isMimo ? 'whitespace-pre-wrap' : ''} style={{ color: isError ? '#f85149' : isDone || isStep ? '#3fb950' : '#c9d1d9' }}>
                       {isStep ? <><span className="text-[#3fb950]">✓</span> {log.msg}</> : isDone ? <><Confetti className="w-4 h-4 inline text-[#3fb950]" /> {log.msg}</> : log.msg}
                     </span>
                   </div>}
                </div>
              )
            })}
            {workflowDrawer?.status === 'processing' && (
              <div className="flex gap-2 mt-1">
                <span className="text-[#484f58]">{new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                <span className="text-[#22c55e]">$</span>
                <span className="animate-pulse text-[#22c55e]">█</span>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
