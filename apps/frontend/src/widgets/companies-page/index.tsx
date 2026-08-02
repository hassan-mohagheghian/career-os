'use client'

import { useCallback, useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useCompanies } from '@/features/companies/hooks/useCompanies'
import { usePending } from '@/shared/hooks/usePending'
import { useWorkflow } from '@/shared/hooks/useWorkflow'
import CompanyDrawer from '@/features/companies/components/CompanyDrawer'
import WorkflowTerminal from '@/shared/components/WorkflowTerminal'
import { setSearchParam, getSearchParam } from '@/shared/lib/url'

const API = '/api'

const CompaniesPageContent = dynamic(
  () => import('@/features/companies/components/CompaniesPage').then(m => ({ default: m.default || m })),
  { ssr: false }
)

function CompaniesPageAdapter() {
  const { companies, fetchCompanies, deleteCompany, reprocessCompany } = useCompanies()
  const [companyDrawer, setCompanyDrawer] = useState<any>(null)

  const {
    pending, deletePending, processPending, resetPending, pausePending,
  } = usePending(() => { fetchCompanies() })

  const {
    workflowDrawer, workflowLogs, workflowEndRef,
    openWorkflow, closeWorkflow,
  } = useWorkflow()

  const openDrawer = useCallback(async (num: number) => {
    window.dispatchEvent(new CustomEvent('openJob', { detail: num }))
  }, [])

  const openCompanyDrawer = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API}/companies/${id}`)
      const data = await res.json()
      setCompanyDrawer(data)
      setSearchParam('company', id)
    } catch (e) {
      console.error('Failed to load company', e)
    }
  }, [])

  const handleDeleteCompany = useCallback(async (id: number) => {
    await deleteCompany(id)
    setCompanyDrawer(null)
    setSearchParam('company', null)
  }, [deleteCompany])

  const handleReprocessCompany = useCallback(async (id: number) => {
    await reprocessCompany(id)
    setCompanyDrawer(null)
    setSearchParam('company', null)
  }, [reprocessCompany])

  useEffect(() => {
    const companyId = getSearchParam('company')
    if (companyId) {
      openCompanyDrawer(companyId)
    }
  }, [])

  return (
    <>
      <CompaniesPageContent
        companies={companies}
        deepLinkId={null}
        onClearDeepLink={() => {}}
        onRefresh={fetchCompanies}
        onOpenJob={openDrawer}
        onNavigateToJob={(num: number) => {
          window.location.href = `/jobs`
          setTimeout(() => openDrawer(num), 200)
        }}
        onOpenCompany={openCompanyDrawer}
        pending={pending}
        deletePending={deletePending}
        processPending={processPending}
        resetPending={resetPending}
        moveToCreated={resetPending}
        pausePending={pausePending}
        openWorkflow={openWorkflow}
      />

      <CompanyDrawer
        company={companyDrawer}
        onClose={() => { setCompanyDrawer(null); setSearchParam('company', null) }}
        onDelete={handleDeleteCompany}
        onReprocess={handleReprocessCompany}
        onOpenJob={(num: number) => openDrawer(num)}
        onNavigateToJob={(num: number) => {
          setTimeout(() => openDrawer(num), 100)
        }}
        onViewAllJobs={() => {
          setCompanyDrawer(null)
          setSearchParam('company', null)
        }}
      />

      <WorkflowTerminal
        workflowDrawer={workflowDrawer}
        workflowLogs={workflowLogs}
        workflowEndRef={workflowEndRef}
        onClose={closeWorkflow}
      />
    </>
  )
}

export default function CompaniesPageWidget() {
  return (
    <MainLayout>
      <CompaniesPageAdapter />
    </MainLayout>
  )
}
