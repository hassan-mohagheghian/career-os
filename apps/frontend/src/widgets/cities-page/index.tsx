'use client'

import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useCitiesInfiniteQuery } from '@/entities/city/hooks'

const CitiesPageContent = dynamic(
  () => import('@/features/cities-v2/components/CitiesPage').then(m => ({ default: m.CitiesPage })),
  { ssr: false }
)

function CitiesPageAdapter() {
  const {
    items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage,
    isError, error, refetch, isRefetching,
    query, setQuery, sort, order, handleHeaderSort,
  } = useCitiesInfiniteQuery()

  return (
    <CitiesPageContent
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
      isRefreshing={isRefetching}
      query={query}
      onQueryChange={setQuery}
      sort={sort}
      order={order}
      onSortChange={handleHeaderSort}
    />
  )
}

export default function CitiesPageWidget() {
  return (
    <MainLayout>
      <CitiesPageAdapter />
    </MainLayout>
  )
}