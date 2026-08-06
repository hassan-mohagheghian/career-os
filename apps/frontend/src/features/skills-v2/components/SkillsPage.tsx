'use client'

import { useCallback } from 'react'
import type { SkillListItem } from '@/entities/skill/types'
import { Button } from '@/shared/ui/button'
import { SkillsHeader } from './SkillsHeader'
import { SkillsToolbar } from './SkillsToolbar'
import { SkillsTable } from './SkillsTable'
import { SkillDetailDrawer } from './SkillDetailDrawer'
import { SkillEditDrawer } from './SkillEditDrawer'
import AddSkillDrawer from './AddSkillDrawer'
import { useCreateSkill } from '@/entities/skill/hooks'
import { toast } from 'sonner'

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
  query: string
  onQueryChange: (value: string) => void
  sort: string
  onSortChange: (value: string) => void
  order: 'asc' | 'desc'
  filterCategory: string
  onFilterCategoryChange: (value: string) => void
  activeFilterCount: number
  onClearFilters: () => void
  onViewDetails: (id: number) => void
  onEdit: (id: number) => void
  onDelete: (id: number) => void
  addSkillDrawerOpen: boolean
  onAddSkillDrawerOpenChange: (open: boolean) => void
  detailSkillId: number | null
  onDetailSkillIdChange: (id: number | null) => void
  editSkillId: number | null
  onEditSkillIdChange: (id: number | null) => void
}

export function SkillsPage({
  items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, onFetchNextPage,
  isError, error, onRefetch,
  query, onQueryChange,
  sort, onSortChange, order,
  filterCategory, onFilterCategoryChange,
  activeFilterCount, onClearFilters,
  onViewDetails, onEdit, onDelete,
  addSkillDrawerOpen, onAddSkillDrawerOpenChange,
  detailSkillId, onDetailSkillIdChange,
  editSkillId, onEditSkillIdChange,
}: SkillsPageProps) {
  const { createSkill, submitting, error: createError, clearError } = useCreateSkill()

  const handleCreateSkill = useCallback(async (data: { name: string; level: number; roles: string; path: string; category: string }) => {
    const ok = await createSkill({
      name: data.name,
      level: data.level,
      roles: data.roles,
      path: data.path,
      category: data.category,
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
      />
      <SkillsToolbar
        query={query}
        onQueryChange={onQueryChange}
        filterCategory={filterCategory}
        onFilterCategoryChange={onFilterCategoryChange}
        activeFilterCount={activeFilterCount}
        onClearFilters={onClearFilters}
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
        onRefresh={onRefetch}
      />
      <SkillEditDrawer
        skillId={editSkillId}
        onOpenChange={onEditSkillIdChange}
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
