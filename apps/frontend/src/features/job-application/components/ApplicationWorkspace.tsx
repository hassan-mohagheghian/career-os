'use client'

import { useEffect, useState, useCallback } from 'react'
import { CircleNotch, PaperPlaneTilt } from '@phosphor-icons/react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { jobApi } from '@/entities/job/api'
import type { JobDetail } from '@/entities/job/types'
import type { ApplicationDetail, ApplicationDocumentType } from '@/entities/application/types'
import {
  useApplicationByJobQuery,
  useCreateApplicationMutation,
  useGenerateDocumentMutation,
  useGeneratePreparationMutation,
} from '@/entities/application/hooks'
import { useApplicationGeneration } from '../hooks/useApplicationGeneration'
import { WorkspaceHeader } from './WorkspaceHeader'
import { ApplicationTracker } from './ApplicationTracker'
import { PreparationPlan } from './PreparationPlan'
import { ApplicationDocuments } from './ApplicationDocuments'
import { GenerationProgress } from './GenerationProgress'
import { Button } from '@/shared/ui/button'

interface ApplicationWorkspaceProps {
  jobId: string
}

function ApplicationSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-3">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">{title}</p>
      {children}
    </div>
  )
}

function EmptyState({ onCreate, pending }: { onCreate: () => void; pending: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <PaperPlaneTilt className="w-10 h-10 text-muted-foreground/50" />
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">No application yet</p>
        <p className="text-xs text-muted-foreground max-w-md">
          Track this job as an application to prepare, generate a tailored resume and cover letter,
          and schedule follow-ups.
        </p>
      </div>
      <Button onClick={onCreate} disabled={pending} className="gap-1.5">
        {pending ? <CircleNotch className="w-4 h-4 animate-spin" /> : <PaperPlaneTilt className="w-4 h-4" />}
        Create Application
      </Button>
    </div>
  )
}

export function ApplicationWorkspace({ jobId }: ApplicationWorkspaceProps) {
  const {
    data: job,
    isLoading: jobLoading,
    isError: jobError,
  } = useQuery<JobDetail>({
    queryKey: ['job-detail', jobId],
    queryFn: () => jobApi.getDetail(jobId),
    enabled: !!jobId,
  })

  const {
    data: application,
    isLoading: applicationLoading,
    isError: applicationError,
    refetch: refetchApplication,
  } = useApplicationByJobQuery(jobId)

  const createApplication = useCreateApplicationMutation()
  const generatePreparation = useGeneratePreparationMutation()
  const generateDocument = useGenerateDocumentMutation()

  const [localApplication, setLocalApplication] = useState<ApplicationDetail | null>(null)
  const [generatingType, setGeneratingType] = useState<ApplicationDocumentType | null>(null)

  const app = localApplication ?? application ?? null
  const { generation, clearGeneration } = useApplicationGeneration(app?.id ?? null)

  useEffect(() => {
    if (createApplication.data) setLocalApplication(createApplication.data)
  }, [createApplication.data])

  useEffect(() => {
    if (application) setLocalApplication(null)
  }, [application])

  const handleCreate = () => {
    createApplication.mutate(jobId, {
      onSuccess: () => toast.success('Application created'),
      onError: () => toast.error('Failed to create application'),
    })
  }

  const handleGeneratePreparation = useCallback(() => {
    if (!app) return
    generatePreparation.mutate(app.id, {
      onSuccess: (response) => {
        setGeneratingType(null)
        toast.success('Preparation generation queued')
        void response
      },
      onError: () => toast.error('Failed to queue preparation generation'),
    })
  }, [app, generatePreparation])

  const handleGenerateDocument = useCallback(
    (documentType: ApplicationDocumentType) => {
      if (!app) return
      generateDocument.mutate(
        { applicationId: app.id, documentType },
        {
          onSuccess: () => {
            setGeneratingType(null)
            toast.success('Document generation queued')
          },
          onError: () => toast.error('Failed to queue document generation'),
        },
      )
      setGeneratingType(documentType)
    },
    [app, generateDocument],
  )

  const handleRefetch = useCallback(() => {
    refetchApplication()
  }, [refetchApplication])

  useEffect(() => {
    if (generation?.status === 'completed' || generation?.status === 'failed') {
      handleRefetch()
    }
  }, [generation?.status, handleRefetch])

  if (jobLoading || applicationLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
      </div>
    )
  }

  if (jobError || !job) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-red-500">Unable to load the job.</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
      <WorkspaceHeader
        job={job}
        applicationStatus={app?.status ?? 'recommended'}
      />

      {generation && (
        <GenerationProgress generation={generation} onDismiss={clearGeneration} />
      )}

      {!app && (
        <EmptyState onCreate={handleCreate} pending={createApplication.isPending} />
      )}

      {app && (
        <>
          <ApplicationSection title="Application">
            <ApplicationTracker application={app} />
          </ApplicationSection>

          <ApplicationSection title="Preparation">
            <PreparationPlan
              applicationId={app.id}
              preparation={app.preparation}
              generating={generatePreparation.isPending}
              onGenerate={handleGeneratePreparation}
            />
          </ApplicationSection>

          <ApplicationSection title="Documents">
            <ApplicationDocuments
              application={app}
              generatingType={generatingType}
              onGenerate={handleGenerateDocument}
            />
          </ApplicationSection>
        </>
      )}
    </div>
  )
}
