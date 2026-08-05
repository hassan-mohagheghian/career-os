'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useState, useCallback, useMemo, useEffect } from 'react'
import { useCompaniesInfiniteQuery, usePendingCompaniesQuery } from '@/entities/company/hooks'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import { toast } from 'sonner'
import { setSearchParam, getSearchParam } from '@/shared/lib/url'

const CompaniesPageContent = dynamic(
  () => import('@/features/companies-v2/components/CompaniesPage').then(m => ({ default: m.CompaniesPage })),
  { ssr: false }
)

function CompaniesPageAdapter() {
  const [queueDrawerOpen, setQueueDrawerOpen] = useState(false)
  const [addCompanyDrawerOpen, setAddCompanyDrawerOpen] = useState(false)
  const [detailCompanyId, setDetailCompanyId] = useState<string | null>(null)
  const [editCompanyId, setEditCompanyId] = useState<string | null>(null)
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()

  const {
    items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage,
    isError, error, refetch,
    query, setQuery,
    sort, order, handleHeaderSort,
    filterIndustry, setFilterIndustry,
    activeFilterCount, clearFilters,
    deleteMutation, reprocessMutation,
  } = useCompaniesInfiniteQuery()

  const { data: pendingItems } = usePendingCompaniesQuery()
  const pendingTotal = pendingItems?.length ?? 0

  const navigateToJobs = useCallback(() => {
    window.location.href = '/jobs'
  }, [])

  const handleViewDetails = useCallback((id: string) => {
    setDetailCompanyId(id)
    setSearchParam('company', id)
  }, [])

  const handleEdit = useCallback((id: string) => {
    setEditCompanyId(id)
  }, [])

  const handleDelete = useCallback(async (id: string) => {
    const ok = await showConfirm(
      'Delete Company',
      'Permanently delete this company and all its intelligence data?',
      'Delete',
    )
    if (!ok) return
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast.success('Company deleted')
        setDetailCompanyId((current) => (current === id ? null : current))
        setEditCompanyId((current) => (current === id ? null : current))
        setSearchParam('company', null)
      },
      onError: () => {
        toast.error('Failed to delete company')
      },
    })
  }, [showConfirm, deleteMutation])

  const handleReprocess = useCallback((id: string) => {
    reprocessMutation.mutate(id, {
      onSuccess: () => {
        toast.success('Company queued for reprocessing')
        setQueueDrawerOpen(true)
      },
      onError: () => {
        toast.error('Failed to reprocess company')
      },
    })
  }, [reprocessMutation])

  useEffect(() => {
    const companyId = getSearchParam('company')
    if (companyId) {
      setDetailCompanyId(companyId)
    }
  }, [])

  useEffect(() => {
    if (detailCompanyId === null) setSearchParam('company', null)
  }, [detailCompanyId])

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <CompaniesPageContent
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
        filterIndustry={filterIndustry}
        onFilterIndustryChange={setFilterIndustry}
        activeFilterCount={activeFilterCount}
        onClearFilters={clearFilters}
        onViewDetails={handleViewDetails}
        onReprocess={handleReprocess}
        onEdit={handleEdit}
        onDelete={handleDelete}
        pendingTotal={pendingTotal}
        queueDrawerOpen={queueDrawerOpen}
        onQueueDrawerOpenChange={setQueueDrawerOpen}
        addCompanyDrawerOpen={addCompanyDrawerOpen}
        onAddCompanyDrawerOpenChange={setAddCompanyDrawerOpen}
        detailCompanyId={detailCompanyId}
        onDetailCompanyIdChange={(id) => {
          setDetailCompanyId(id)
          if (id === null) setSearchParam('company', null)
        }}
        editCompanyId={editCompanyId}
        onEditCompanyIdChange={setEditCompanyId}
        onOpenJob={navigateToJobs}
        onNavigateToJob={navigateToJobs}
        onViewAllJobs={navigateToJobs}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
    </div>
  )
}

export default function CompaniesPageWidget() {
  return (
    <MainLayout>
      <CompaniesPageAdapter />
    </MainLayout>
  )
}
