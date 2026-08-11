'use client'

import { CircleNotch, CheckCircle, XCircle, Warning } from '@phosphor-icons/react'
import { Progress } from '@/shared/ui/progress'
import type { ApplicationGenerationState } from '../hooks/useApplicationGeneration'

interface GenerationProgressProps {
  generation: ApplicationGenerationState
  onDismiss?: () => void
}

const artifactLabels: Record<string, string> = {
  preparation: 'Preparation plan',
  tailored_resume: 'Tailored resume',
  cover_letter: 'Cover letter',
}

export function GenerationProgress({ generation, onDismiss }: GenerationProgressProps) {
  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {generation.status === 'failed' ? (
            <XCircle className="w-4 h-4 text-red-500 shrink-0" />
          ) : generation.status === 'completed' ? (
            <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
          ) : (
            <CircleNotch className="w-4 h-4 text-emerald-500 animate-spin shrink-0" />
          )}
          <p className="text-xs font-medium text-foreground truncate">
            {generation.artifact ? artifactLabels[generation.artifact] ?? generation.artifact : 'AI generation'}
            {generation.status === 'running' ? ' in progress' : ''}
          </p>
        </div>
        {onDismiss && generation.status !== 'running' && (
          <button
            type="button"
            onClick={onDismiss}
            className="text-2xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Dismiss
          </button>
        )}
      </div>

      {generation.status === 'running' && (
        <>
          <Progress value={generation.progress ?? 0} />
          <p className="text-2xs text-muted-foreground flex items-center gap-1.5">
            {generation.currentStep ?? 'Processing…'}
            {generation.progress !== null && (
              <span className="shrink-0">{Math.round(generation.progress)}%</span>
            )}
          </p>
        </>
      )}

      {generation.status === 'completed' && (
        <p className="text-2xs text-green-600 flex items-center gap-1.5">
          <CheckCircle className="w-3 h-3" /> Generated successfully.
        </p>
      )}

      {generation.status === 'failed' && generation.error && (
        <p className="text-2xs text-red-500 flex items-start gap-1.5">
          <Warning className="w-3 h-3 mt-0.5 shrink-0" />
          <span className="break-words">{generation.error}</span>
        </p>
      )}
    </div>
  )
}
