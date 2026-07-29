import { Check } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/shared/ui/tooltip'

export interface StepConfig {
  key: string
  icon: React.ReactNode
  label: string
}

export default function StepProgress({ steps, values, nextStep }: {
  steps: StepConfig[]
  values: (number | undefined)[]
  nextStep: number
}) {
  return (
    <div className="flex gap-1 mb-1 min-w-0">
      {steps.map((step, i) => {
        const done = values[i] === 1
        const isActive = i === nextStep && !done
        return (
          <div key={i} className="flex-1 min-w-0 flex justify-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={cn(
                  'w-4 h-4 rounded-full border shrink-0 flex items-center justify-center cursor-default',
                  done ? 'bg-green-500 border-green-500 text-white' :
                  isActive ? 'bg-primary border-primary text-primary-foreground animate-pulse' :
                  'bg-background border-border text-muted-foreground',
                )}>
                  {done ? <Check className="w-2 h-2" /> : step.icon}
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-2xs px-2 py-1">
                {done ? `${step.label} — done` : isActive ? `${step.label} — in progress...` : step.label}
              </TooltipContent>
            </Tooltip>
          </div>
        )
      })}
    </div>
  )
}
