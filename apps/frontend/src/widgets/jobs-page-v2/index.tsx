'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useState, useCallback, useMemo } from 'react'
import { useJobsInfiniteQuery } from '@/features/jobs-v2/hooks/useJobsInfiniteQuery'
import { useProcessingEvents } from '@/shared/hooks/useProcessingEvents'
import { processingApi } from '@/entities/processing/api'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import { toast } from 'sonner'

const JobsPageContent = dynamic(
  () => import('@/features/jobs-v2/components/JobsPage').then(m => ({ default: m.JobsPage })),
  { ssr: false }
)

function JobsPageV2Adapter() {
  const [queueDrawerOpen, setQueueDrawerOpen] = useState(false)
  const [queueReloadKey, setQueueReloadKey] = useState(0)
  const [addJobDrawerOpen, setAddJobDrawerOpen] = useState(false)
  const [detailJobId, setDetailJobId] = useState<string | null>(null)
  const [editJobId, setEditJobId] = useState<string | null>(null)
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()

  const {
    items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage,
    isError, error, refetch,
    query, setQuery,
    sort, order, handleHeaderSort,
    filterProcessingStatus, setFilterProcessingStatus,
    filterLocation, setFilterLocation,
    filterRemote, setFilterRemote,
    filterVisa, setFilterVisa,
    activeFilterCount, clearFilters,
    processMutation,
    deleteMutation,
  } = useJobsInfiniteQuery()

  useProcessingEvents()

  const processingCount = useMemo(() => {
    return items.filter(i => {
      const s = i.latest_processing_execution?.status
      return s === 'queued' || s === 'running' || s === 'starting'
    }).length
  }, [items])

  const handleProcessV2 = useCallback((id: string) => {
    processMutation.mutate(id, {
      onSettled: () => setQueueReloadKey(k => k + 1),
    })
    setQueueDrawerOpen(true)
  }, [processMutation])

  const handleViewDetails = useCallback((id: string) => {
    setDetailJobId(id)
  }, [])

  const handleEdit = useCallback((id: string) => {
    setEditJobId(id)
  }, [])

  const handleDelete = useCallback(async (id: string) => {
    const ok = await showConfirm(
      'Delete Job',
      'Permanently delete this job and all its processing data?',
      'Delete',
    )
    if (!ok) return
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast.success('Job deleted')
        setDetailJobId((current) => (current === id ? null : current))
        setEditJobId((current) => (current === id ? null : current))
      },
      onError: () => {
        toast.error('Failed to delete job')
      },
    })
  }, [showConfirm, deleteMutation])

  const handleRetry = useCallback((id: string) => {
    processMutation.mutate(id, {
      onSettled: () => setQueueReloadKey(k => k + 1),
    })
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
        filterLocation={filterLocation}
        onFilterLocationChange={setFilterLocation}
        filterRemote={filterRemote}
        onFilterRemoteChange={setFilterRemote}
        filterVisa={filterVisa}
        onFilterVisaChange={setFilterVisa}
        activeFilterCount={activeFilterCount}
        onClearFilters={clearFilters}
        onProcessV2={handleProcessV2}
        onViewDetails={handleViewDetails}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRetry={handleRetry}
        onCancel={handleCancel}
        isProcessing={processMutation.isPending}
        queueDrawerOpen={queueDrawerOpen}
        onQueueDrawerOpenChange={setQueueDrawerOpen}
        queueReloadKey={queueReloadKey}
        addJobDrawerOpen={addJobDrawerOpen}
        onAddJobDrawerOpenChange={setAddJobDrawerOpen}
        onJobQueued={() => setQueueReloadKey(k => k + 1)}
        detailJobId={detailJobId}
        onDetailJobIdChange={setDetailJobId}
        editJobId={editJobId}
        onEditJobIdChange={setEditJobId}
        processingCount={processingCount}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
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
