'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import dynamic from 'next/dynamic'
import MainLayout from '@/widgets/main-layout'
import { useJobs } from '@/features/jobs/hooks/useJobs'
import { usePending } from '@/shared/hooks/usePending'
import { useCompanies } from '@/features/companies/hooks/useCompanies'
import { useResume } from '@/features/jobs/hooks/useResume'
import { useWorkflow } from '@/shared/hooks/useWorkflow'
import { useSocketIO } from '@/shared/hooks/useSocketIO'
import ConfirmDialog from '@/shared/components/ConfirmDialog'
import DuplicateJobDialog from '@/shared/components/DuplicateJobDialog'
import WorkflowTerminal from '@/shared/components/WorkflowTerminal'
import JobDrawer from '@/features/jobs/components/drawer/JobDrawer'
import CompanyDrawer from '@/features/companies/components/CompanyDrawer'
import { toast } from 'sonner'
import { setSearchParam, getSearchParam } from '@/shared/lib/url'

const API = '/api'

const JobsPageContent = dynamic(
  () => import('@/features/jobs/components/JobsPage').then(m => ({ default: m.default || m })),
  { ssr: false }
)

function JobsPageAdapter() {
  const socket = useSocketIO()
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [confirmDialog, setConfirmDialog] = useState<any>(null)
  const [duplicateJob, setDuplicateJob] = useState<any>(null)
  const [drawer, setDrawer] = useState<any>(null)
  const [drawerTab, setDrawerTab] = useState('details')
  const [companyDrawer, setCompanyDrawer] = useState<any>(null)

  const {
    workflowDrawer, workflowLogs, workflowEndRef,
    openWorkflow, closeWorkflow,
  } = useWorkflow()

  const {
    pending, urlInput, setUrlInput, urlError, setUrlError,
    submitting, processImmediately, setProcessImmediately,
    submitUrl, deletePending, processPending, resetPending, pausePending,
  } = usePending(() => { refreshJobs(); fetchCompanies() })

  const {
    jobs, setJobs, summaries, setSummaries, jobsTotal, jobAgg,
    loadingMore, jobsScrollRef, jobsSentinelRef,
    sortBy, setSortBy, sortDir, setSortDir,
    filterCities, setFilterCities,
    filterCompanies, setFilterCompanies,
    filterTech, setFilterTech,
    filterMatches, setFilterMatches,
    filterWorkTypes, setFilterWorkTypes,
    filterEmploymentTypes, setFilterEmploymentTypes,
    filterResponseStatus, setFilterResponseStatus,
    filterApplied, setFilterApplied,
    filterScores, setFilterScores,
    activeFilterCount, allCities, allCompanies, filteredJobs,
    refreshJobs, loadMoreJobs, fetchJobs, fetchSummaries,
    deleteJob, requeueJob, rescoreJob, updateJob, clearFilters,
  } = useJobs()

  const {
    companies, fetchCompanies, deleteCompany, reprocessCompany,
  } = useCompanies()

  const {
    resumes, setResumes, linkedinProfiles, activeGens, generationResult,
    fetchResumes, fetchLinkedin, generateResume, generateCover, cancelGeneration,
  } = useResume()

  useEffect(() => {
    if (!generationResult) return
    const { type, content, content_id, job_num, title } = generationResult
    if (type === 'resume') {
      setDrawer((prev: any) => prev ? { ...prev, resume: { id: content_id, content, job_num, title } } : null)
    } else if (type === 'cover') {
      setDrawer((prev: any) => prev ? { ...prev, coverLetter: { id: content_id, content, job_num, title } } : null)
    }
  }, [generationResult])

  const deepLinked = useRef(false)

  useEffect(() => {
    if (deepLinked.current || !jobs) return
    deepLinked.current = true
    const jobNum = getSearchParam('job')
    const companyId = getSearchParam('company')
    if (jobNum) {
      openDrawerHandler(Number(jobNum))
    } else if (companyId) {
      openCompanyDrawer(companyId)
    }
  }, [jobs])

  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({})

  const showConfirm = useCallback((title: string, message: string, confirmLabel: string, variant = 'danger') => {
    return new Promise<boolean>((resolve) => {
      setConfirmDialog({ title, message, confirmLabel, variant, resolve })
    })
  }, [])

  const handleDeleteJob = useCallback(async (num: number) => {
    const ok = await showConfirm('Delete Job', `Permanently delete job #${num}? This cannot be undone.`, 'Delete Forever')
    if (!ok) return
    await deleteJob(num)
  }, [showConfirm, deleteJob])

  const handleRequeueJob = useCallback(async (num: number) => {
    const ok = await showConfirm('Reprocess Job', `Reprocess job #${num} from scratch? The current version will be permanently deleted.`, 'Reprocess')
    if (!ok) return
    await requeueJob(num)
  }, [showConfirm, requeueJob])

  const handleUpdateJob = useCallback(async (num: number, fields: Record<string, any>) => {
    const updated = await updateJob(num, fields)
    if (updated) {
      setDrawer((prev: any) => prev && prev.job?.num === num ? { ...prev, job: { ...prev.job, ...updated } } : prev)
    }
  }, [updateJob])

  const openDrawerHandler = useCallback(async (num: number) => {
    if (!jobs) return
    const j = jobs.find((x: any) => x.num === num)
    const s = summaries?.find((x: any) => x.num === num)
    let fullJob = j
    try {
      const res = await fetch(`${API}/jobs/${num}`)
      if (res.ok) fullJob = await res.json()
    } catch {}
    setDrawer({
      job: fullJob,
      summary: s,
      resume: fullJob?.resume || null,
      coverLetter: fullJob?.coverLetter || null,
    })
    setDrawerTab('details')
    setCompanyDrawer(null)
    setSearchParam('job', String(num))
  }, [jobs, summaries])

  const openCompanyDrawer = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API}/companies/${id}`)
      const data = await res.json()
      setCompanyDrawer(data)
      setDrawer(null)
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

  if (jobs === null) {
    return (
      <div className="flex items-center justify-center h-screen text-muted-foreground">
        Loading...
      </div>
    )
  }

  return (
    <>
      <div className="flex gap-2 h-[calc(100vh-80px)]">
        <div className="flex-1 flex flex-col min-w-0">
          <JobsPageContent
            pending={pending}
            jobs={jobs}
            filteredJobs={filteredJobs}
            jobsTotal={jobsTotal}
            filteredJobsCount={filteredJobs.length}
            urlInput={urlInput}
            setUrlInput={setUrlInput}
            urlError={urlError}
            setUrlError={setUrlError}
            submitting={submitting}
            processImmediately={processImmediately}
            setProcessImmediately={setProcessImmediately}
            sortBy={sortBy}
            setSortBy={setSortBy}
            sortDir={sortDir}
            setSortDir={setSortDir}
            filterTech={filterTech}
            setFilterTech={setFilterTech}
            filterCities={filterCities}
            setFilterCities={setFilterCities}
            filterCompanies={filterCompanies}
            setFilterCompanies={setFilterCompanies}
            filterMatches={filterMatches}
            setFilterMatches={setFilterMatches}
            filterWorkTypes={filterWorkTypes}
            setFilterWorkTypes={setFilterWorkTypes}
            filterEmploymentTypes={filterEmploymentTypes}
            setFilterEmploymentTypes={setFilterEmploymentTypes}
            filterResponseStatus={filterResponseStatus}
            setFilterResponseStatus={setFilterResponseStatus}
            filterApplied={filterApplied}
            setFilterApplied={setFilterApplied}
            filterScores={filterScores}
            setFilterScores={setFilterScores}
            allCities={allCities}
            allCompanies={allCompanies}
            activeFilterCount={activeFilterCount}
            collapsedSections={collapsedSections}
            setCollapsedSections={setCollapsedSections}
            loadingMore={loadingMore}
            jobsScrollRef={jobsScrollRef}
            jobsSentinelRef={jobsSentinelRef}
            submitUrl={submitUrl}
            deletePending={deletePending}
            processPending={processPending}
            resetPending={resetPending}
            moveToCreated={resetPending}
            pausePending={pausePending}
            openWorkflow={openWorkflow}
            rescoreJob={rescoreJob}
            deleteJob={handleDeleteJob}
            requeueJob={handleRequeueJob}
            openDrawer={openDrawerHandler}
            refreshJobs={refreshJobs}
            clearFilters={clearFilters}
            loadMoreJobs={loadMoreJobs}
            onOpenCompany={openCompanyDrawer}
          />
        </div>
      </div>

      <JobDrawer
        drawer={drawer}
        drawerTab={drawerTab}
        activeGens={activeGens}
        companies={companies}
        onClose={() => { setDrawer(null); setSearchParam('job', null) }}
        onSetDrawerTab={setDrawerTab}
        onRescoreJob={rescoreJob}
        onRequeueJob={handleRequeueJob}
        onUpdateJob={handleUpdateJob}
        onSetToast={(msg: string) => toast.success(msg)}
        onGenerateResume={(num: number) => generateResume(num)}
        onGenerateCover={(num: number) => generateCover(num)}
        onCancelGeneration={cancelGeneration}
        onLinkCompany={async (num: number, companyId: string) => {
          await fetch(`${API}/jobs/${num}/link-company`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: companyId }),
          })
          const res = await fetch(`${API}/jobs/${num}`)
          const updated = await res.json()
          setDrawer((prev: any) => (prev ? { ...prev, job: updated } : null))
        }}
        onOpenCompany={(id: string) => openCompanyDrawer(id)}
        onNavigateToCompany={(id: string) => {
          setTimeout(() => openCompanyDrawer(id), 100)
        }}
      />

      <CompanyDrawer
        company={companyDrawer}
        onClose={() => { setCompanyDrawer(null); setSearchParam('company', null) }}
        onDelete={handleDeleteCompany}
        onReprocess={handleReprocessCompany}
        onOpenJob={(num: number) => openDrawerHandler(num)}
        onNavigateToJob={(num: number) => {
          setTimeout(() => openDrawerHandler(num), 100)
        }}
        onViewAllJobs={(companyName: string) => {
          setCompanyDrawer(null)
          setSearchParam('company', null)
          setFilterCompanies([companyName])
        }}
      />

      <ConfirmDialog
        dialog={confirmDialog}
        onClose={() => setConfirmDialog(null)}
      />

      <DuplicateJobDialog
        duplicateJob={duplicateJob}
        setDuplicateJob={setDuplicateJob}
        onRescore={async (num: number) => {
          await rescoreJob(num)
        }}
        onReprocess={async (num: number) => {
          await requeueJob(num)
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

export default function JobsPageWidget() {
  return (
    <MainLayout>
      <JobsPageAdapter />
    </MainLayout>
  )
}
