'use client'

import { useCallback } from 'react'
import type { JobListItem, ProcessingStatus } from '@/entities/job/types'
import { Button } from '@/shared/ui/button'
import { JobsHeader } from './JobsHeader'
import { JobsToolbar } from './JobsToolbar'
import { JobsTable } from './JobsTable'
import { ProcessingDrawer } from './ProcessingDrawer'
import { JobDetailDrawer } from './JobDetailDrawer'
import AddJobDrawer from '@/features/jobs/components/AddJobDrawer'
import { useCreateJob } from '@/features/jobs/hooks/useCreateJob'
import { toast } from 'sonner'

interface JobsPageProps {
  items: JobListItem[]
  total: number
  loadedCount: number
  isLoading: boolean
  isFetchingNextPage: boolean
  hasNextPage: boolean
  onFetchNextPage: () => void
  isError: boolean
  error: Error | null
  onRefetch: () => void
  query: string
  onQueryChange: (value: string) => void
  sort: string
  onSortChange: (value: string) => void
  order: 'asc' | 'desc'
  filterProcessingStatus: ProcessingStatus | ''
  onFilterProcessingStatusChange: (value: ProcessingStatus | '') => void
  filterRemote: boolean | ''
  onFilterRemoteChange: (value: boolean | '') => void
  filterVisa: boolean | ''
  onFilterVisaChange: (value: boolean | '') => void
  activeFilterCount: number
  onClearFilters: () => void
  onProcessV2: (id: string) => void
  onViewDetails: (id: string) => void
  onRetry?: (id: string) => void
  onCancel?: (id: string) => void
  isProcessing: boolean
  queueDrawerOpen: boolean
  onQueueDrawerOpenChange: (open: boolean) => void
  addJobDrawerOpen: boolean
  onAddJobDrawerOpenChange: (open: boolean) => void
  detailJobId: string | null
  onDetailJobIdChange: (id: string | null) => void
  processingCount: number
}

export function JobsPage({
  items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, onFetchNextPage,
  isError, error, onRefetch,
  query, onQueryChange,
  sort, onSortChange, order,
  filterProcessingStatus, onFilterProcessingStatusChange,
  filterRemote, onFilterRemoteChange,
  filterVisa, onFilterVisaChange,
  activeFilterCount, onClearFilters,
  onProcessV2, onViewDetails, onRetry, onCancel, isProcessing,
  queueDrawerOpen, onQueueDrawerOpenChange,
  addJobDrawerOpen, onAddJobDrawerOpenChange,
  detailJobId, onDetailJobIdChange,
  processingCount,
}: JobsPageProps) {
  const { createJob, submitting, error: createError, clearError } = useCreateJob()

  const handleCreateJob = useCallback(async (data: any) => {
    const result = await createJob(data)
    if (result) {
      toast.success('Job created successfully')
      onAddJobDrawerOpenChange(false)
      onRefetch()
    }
  }, [createJob, onAddJobDrawerOpenChange, onRefetch])

  if (isError) {
    return (
      <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
        <JobsHeader
          total={total}
          loadedCount={loadedCount}
          processingCount={processingCount}
          onOpenQueue={() => onQueueDrawerOpenChange(true)}
          onAddJob={() => onAddJobDrawerOpenChange(true)}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <p className="text-sm text-red-500">Unable to load jobs</p>
            <p className="text-xs text-muted-foreground">{error?.message || 'An unexpected error occurred'}</p>
            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onRefetch}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
      <JobsHeader
        total={total}
        loadedCount={loadedCount}
        processingCount={processingCount}
        onOpenQueue={() => onQueueDrawerOpenChange(true)}
        onAddJob={() => onAddJobDrawerOpenChange(true)}
      />
      <JobsToolbar
        query={query}
        onQueryChange={onQueryChange}
        filterProcessingStatus={filterProcessingStatus}
        onFilterProcessingStatusChange={onFilterProcessingStatusChange}
        filterRemote={filterRemote}
        onFilterRemoteChange={onFilterRemoteChange}
        filterVisa={filterVisa}
        onFilterVisaChange={onFilterVisaChange}
        activeFilterCount={activeFilterCount}
        onClearFilters={onClearFilters}
      />
      <JobsTable
        items={items}
        total={total}
        loadedCount={loadedCount}
        isLoading={isLoading}
        isFetchingNextPage={isFetchingNextPage}
        hasNextPage={hasNextPage}
        onFetchNextPage={onFetchNextPage}
        onProcessV2={onProcessV2}
        onViewDetails={onViewDetails}
        onRetry={onRetry}
        onCancel={onCancel}
        sort={sort}
        order={order}
        onSortChange={onSortChange}
      />
      <ProcessingDrawer
        open={queueDrawerOpen}
        onOpenChange={onQueueDrawerOpenChange}
      />
      <JobDetailDrawer
        jobId={detailJobId}
        onOpenChange={onDetailJobIdChange}
      />      <AddJobDrawer
        open={addJobDrawerOpen}
        onOpenChange={(open) => { onAddJobDrawerOpenChange(open); if (!open) clearError() }}
        onSubmit={handleCreateJob}
        submitting={submitting}
        error={createError}
      />
    </div>
  )
}
