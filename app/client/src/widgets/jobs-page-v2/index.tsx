'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useState, useCallback, useMemo } from 'react'
import { useJobsInfiniteQuery } from '@/features/jobs-v2/hooks/useJobsInfiniteQuery'
import { useProcessingEvents } from '@/shared/hooks/useProcessingEvents'
import { toast } from 'sonner'

const JobsPageContent = dynamic(
  () => import('@/features/jobs-v2/components/JobsPage').then(m => ({ default: m.JobsPage })),
  { ssr: false }
)

function JobsPageV2Adapter() {
  const [queueDrawerOpen, setQueueDrawerOpen] = useState(false)
  const [addJobDrawerOpen, setAddJobDrawerOpen] = useState(false)

  const {
    items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage,
    isError, error, refetch,
    query, setQuery,
    sort, setSort, order, toggleOrder,
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

  const handleLegacyProcess = useCallback((id: string) => {
    toast.success(`Legacy processing started for job #${id}`)
  }, [])

  const handleViewDetails = useCallback((id: string) => {
    toast.info(`Opening details for job #${id}`)
  }, [])

  const handleRetry = useCallback((id: string) => {
    processMutation.mutate(id)
    setQueueDrawerOpen(true)
  }, [processMutation])

  const handleCancel = useCallback((_id: string) => {
    toast.success('Cancelled processing')
  }, [])

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
        onSortChange={setSort}
        order={order}
        onToggleOrder={toggleOrder}
        filterProcessingStatus={filterProcessingStatus}
        onFilterProcessingStatusChange={setFilterProcessingStatus}
        filterRemote={filterRemote}
        onFilterRemoteChange={setFilterRemote}
        filterVisa={filterVisa}
        onFilterVisaChange={setFilterVisa}
        activeFilterCount={activeFilterCount}
        onClearFilters={clearFilters}
        onProcessV2={handleProcessV2}
        onLegacyProcess={handleLegacyProcess}
        onViewDetails={handleViewDetails}
        onRetry={handleRetry}
        onCancel={handleCancel}
        isProcessing={processMutation.isPending}
        queueDrawerOpen={queueDrawerOpen}
        onQueueDrawerOpenChange={setQueueDrawerOpen}
        addJobDrawerOpen={addJobDrawerOpen}
        onAddJobDrawerOpenChange={setAddJobDrawerOpen}
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
