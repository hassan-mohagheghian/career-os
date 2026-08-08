'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import type { SkillListItem } from '@/entities/skill/types'
import { Button } from '@/shared/ui/button'
import { SkillsHeader } from './SkillsHeader'
import { SkillsToolbar } from './SkillsToolbar'
import { SkillsTable } from './SkillsTable'
import { SkillDetailDrawer } from './SkillDetailDrawer'
import { SkillEditDrawer } from './SkillEditDrawer'
import AddSkillDrawer from './AddSkillDrawer'
import { useCreateSkill, useMergeSkills } from '@/entities/skill/hooks'
import { toast } from 'sonner'
import { MergeSkillDialog } from './MergeSkillDialog'

interface SkillsPageProps {
  items: SkillListItem[]
  total: number
  loadedCount: number
  isLoading: boolean
  isFetchingNextPage: boolean
  hasNextPage: boolean
  onFetchNextPage: () => void
  isError: boolean
  error: Error | null
  onRefetch: () => void
  isRefetching?: boolean
  query: string
  onQueryChange: (value: string) => void
  sort: string
  onSortChange: (value: string) => void
  order: 'asc' | 'desc'
  filterCategories: string[]
  onFilterCategoriesChange: (value: string[]) => void
  categoryOptions: string[]
  filterPinned?: boolean
  onFilterPinnedChange?: (value: boolean) => void
  activeFilterCount: number
  onClearFilters: () => void
  onViewDetails: (id: number) => void
  onEdit: (id: number) => void
  onDelete: (id: number) => void
  onTogglePinned?: (id: number, pinned: boolean) => void
  showPinnedColumn?: boolean
  onTogglePinnedColumn?: (value: boolean) => void
  showSelectColumn?: boolean
  onToggleSelectColumn?: (value: boolean) => void
  addSkillDrawerOpen: boolean
  onAddSkillDrawerOpenChange: (open: boolean) => void
  detailSkillId: number | null
  onDetailSkillIdChange: (id: number | null) => void
  editSkillId: number | null
  onEditSkillIdChange: (id: number | null) => void
}

export function SkillsPage({
  items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, onFetchNextPage,
  isError, error, onRefetch, isRefetching,
  query, onQueryChange,
  sort, onSortChange, order,
  filterCategories, onFilterCategoriesChange, categoryOptions,
  filterPinned = false, onFilterPinnedChange,
  activeFilterCount, onClearFilters,
  onViewDetails, onEdit, onDelete, onTogglePinned,
  showPinnedColumn = true, onTogglePinnedColumn,
  showSelectColumn = false, onToggleSelectColumn,
  addSkillDrawerOpen, onAddSkillDrawerOpenChange,
  detailSkillId, onDetailSkillIdChange,
  editSkillId, onEditSkillIdChange,
}: SkillsPageProps) {
  const { createSkill, submitting, error: createError, clearError } = useCreateSkill()
  const mergeMutation = useMergeSkills()

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [mergeOpen, setMergeOpen] = useState(false)

  useEffect(() => {
    setSelectedIds(new Set())
  }, [query, filterCategories, filterPinned])

  const loadedIds = useMemo(() => new Set(items.map((s) => s.id)), [items])
  useEffect(() => {
    setSelectedIds((prev) => {
      const next = new Set([...prev].filter((id) => loadedIds.has(id)))
      return next.size === prev.size ? prev : next
    })
  }, [loadedIds])

  const handleToggleSelect = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleToggleSelectAll = useCallback((selectAll: boolean) => {
    setSelectedIds(selectAll ? new Set(loadedIds) : new Set())
  }, [loadedIds])

  const handleClearSelection = useCallback(() => setSelectedIds(new Set()), [])

  const selectedSkills = useMemo(
    () => items.filter((s) => selectedIds.has(s.id)),
    [items, selectedIds]
  )

  const handleBulkMerge = useCallback(async (targetId: number) => {
    const sourceIds = [...selectedIds]
    if (sourceIds.length === 0) return
    setMergeOpen(false)
    try {
      await mergeMutation.mutateAsync({ targetId, sourceIds })
      toast.success(`Merged ${sourceIds.length} skill${sourceIds.length !== 1 ? 's' : ''}`)
      setSelectedIds(new Set())
      if (editSkillId != null && sourceIds.includes(editSkillId)) onEditSkillIdChange(null)
    } catch {
      toast.error('Failed to merge skills')
    }
  }, [selectedIds, mergeMutation, editSkillId, onEditSkillIdChange])

  const handleCreateSkill = useCallback(async (data: { name: string; level: number; roles: string; path: string; category: string; categories: string[] }) => {
    const ok = await createSkill({
      name: data.name,
      level: data.level,
      roles: data.roles,
      path: data.path,
      category: data.category,
      categories: data.categories,
    })
    if (ok) {
      toast.success('Skill added')
      onAddSkillDrawerOpenChange(false)
    }
  }, [createSkill, onAddSkillDrawerOpenChange])

  const detailSkill = items.find((s) => s.id === detailSkillId) ?? null

  if (isError) {
    return (
      <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
        <SkillsHeader
          total={total}
          loadedCount={loadedCount}
          onAddSkill={() => onAddSkillDrawerOpenChange(true)}
          onRefresh={onRefetch}
          isRefreshing={isRefetching}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <p className="text-sm text-red-500">Unable to load skills</p>
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
      <SkillsHeader
        total={total}
        loadedCount={loadedCount}
        onAddSkill={() => onAddSkillDrawerOpenChange(true)}
        onRefresh={onRefetch}
        isRefreshing={isRefetching}
      />
      <SkillsToolbar
        query={query}
        onQueryChange={onQueryChange}
        filterCategories={filterCategories}
        onFilterCategoriesChange={onFilterCategoriesChange}
        categoryOptions={categoryOptions}
        filterPinned={filterPinned}
        onFilterPinnedChange={onFilterPinnedChange}
        activeFilterCount={activeFilterCount}
        onClearFilters={onClearFilters}
        showPinnedColumn={showPinnedColumn}
        onTogglePinnedColumn={onTogglePinnedColumn}
        showSelectColumn={showSelectColumn}
        onToggleSelectColumn={onToggleSelectColumn}
        selectedCount={selectedIds.size}
        onMergeSelected={() => setMergeOpen(true)}
        onClearSelection={handleClearSelection}
        mergePending={mergeMutation.isPending}
      />
      <SkillsTable
        items={items}
        total={total}
        loadedCount={loadedCount}
        isLoading={isLoading}
        isFetchingNextPage={isFetchingNextPage}
        hasNextPage={hasNextPage}
        onFetchNextPage={onFetchNextPage}
        onViewDetails={onViewDetails}
        onEdit={onEdit}
        onDelete={onDelete}
        onTogglePinned={onTogglePinned}
        showPinnedColumn={showPinnedColumn}
        showSelectColumn={showSelectColumn}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onToggleSelectAll={handleToggleSelectAll}
        sort={sort}
        order={order}
        onSortChange={onSortChange}
      />
      <SkillDetailDrawer
        skillId={detailSkillId}
        skill={detailSkill}
        onOpenChange={onDetailSkillIdChange}
        onEdit={onEdit}
        onDelete={onDelete}
      />
      <SkillEditDrawer
        skillId={editSkillId}
        onOpenChange={onEditSkillIdChange}
      />
      <MergeSkillDialog
        sources={selectedSkills.map((s) => ({ id: s.id, name: s.name }))}
        open={mergeOpen}
        onOpenChange={setMergeOpen}
        onMerge={handleBulkMerge}
        pending={mergeMutation.isPending}
      />
      <AddSkillDrawer
        open={addSkillDrawerOpen}
        onOpenChange={(open) => { onAddSkillDrawerOpenChange(open); if (!open) clearError() }}
        onSubmit={handleCreateSkill}
        submitting={submitting}
        error={createError}
      />
    </div>
  )
}
