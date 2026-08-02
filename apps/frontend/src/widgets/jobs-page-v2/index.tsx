'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useState, useCallback, useMemo } from 'react'
import { useJobsInfiniteQuery } from '@/features/jobs-v2/hooks/useJobsInfiniteQuery'
import { useProcessingEvents } from '@/shared/hooks/useProcessingEvents'
import { processingApi } from '@/entities/processing/api'
import { toast } from 'sonner'

const JobsPageContent = dynamic(
  () => import('@/features/jobs-v2/components/JobsPage').then(m => ({ default: m.JobsPage })),
  { ssr: false }
)

function JobsPageV2Adapter() {
  const [queueDrawerOpen, setQueueDrawerOpen] = useState(false)
  const [addJobDrawerOpen, setAddJobDrawerOpen] = useState(false)
  const [detailJobId, setDetailJobId] = useState<string | null>(null)
  const [editJobId, setEditJobId] = useState<string | null>(null)

  const {
    items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage,
    isError, error, refetch,
    query, setQuery,
    sort, order, handleHeaderSort,
    filterProcessingStatus, setFilterProcessingStatus,
    filterRemote, setFilterRemote,
    filterVisa, setFilterVisa,
    activeFilterCount, clearFilters,
    processMutation,
  } = useJobsInfiniteQuery()

  useProcessingEvents()

  const processingCount = useMemo(() => {
    return items.filter(i => {
      const s = i.latest_processing_execution?.status
      return s === 'queued' || s === 'running' || s === 'starting'
    }).length
  }, [items])

  const handleProcessV2 = useCallback((id: string) => {
    processMutation.mutate(id)
    setQueueDrawerOpen(true)
  }, [processMutation])

  const handleViewDetails = useCallback((id: string) => {
    setDetailJobId(id)
  }, [])

  const handleEdit = useCallback((id: string) => {
    setEditJobId(id)
  }, [])

  const handleRetry = useCallback((id: string) => {
    processMutation.mutate(id)
    setQueueDrawerOpen(true)
  }, [processMutation])

  const handleCancel = useCallback((id: string) => {
    const job = items.find(j => j.id === id)
    const executionId = job?.latest_processing_execution?.id
    if (!executionId) return
    processingApi.cancel(executionId)
      .then(() => {
        toast.success('Cancelled processing')
        refetch()
      })
      .catch(() => toast.error('Failed to cancel processing'))
  }, [items, refetch])

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <JobsPageContent
        items={items}
        total={total}
        loadedCount={loadedCount}
        isLoading={isLoading}
        isFetchingNextPage={isFetchingNextPage}
        hasNextPage={hasNextPage}
        onFetchNextPage={fetchNextPage}
        isError={isError}
        error={error}
        onRefetch={refetch}
        query={query}
        onQueryChange={setQuery}
        sort={sort}
        onSortChange={handleHeaderSort}
        order={order}
        filterProcessingStatus={filterProcessingStatus}
        onFilterProcessingStatusChange={setFilterProcessingStatus}
        filterRemote={filterRemote}
        onFilterRemoteChange={setFilterRemote}
        filterVisa={filterVisa}
        onFilterVisaChange={setFilterVisa}
        activeFilterCount={activeFilterCount}
        onClearFilters={clearFilters}
        onProcessV2={handleProcessV2}
        onViewDetails={handleViewDetails}
        onEdit={handleEdit}
        onRetry={handleRetry}
        onCancel={handleCancel}
        isProcessing={processMutation.isPending}
        queueDrawerOpen={queueDrawerOpen}
        onQueueDrawerOpenChange={setQueueDrawerOpen}
        addJobDrawerOpen={addJobDrawerOpen}
        onAddJobDrawerOpenChange={setAddJobDrawerOpen}
        detailJobId={detailJobId}
        onDetailJobIdChange={setDetailJobId}
        editJobId={editJobId}
        onEditJobIdChange={setEditJobId}
        processingCount={processingCount}
      />
    </div>
  )
}

export default function JobsPageV2Widget() {
  return (
    <MainLayout>
      <JobsPageV2Adapter />
    </MainLayout>
  )
}
