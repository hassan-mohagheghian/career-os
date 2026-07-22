import { useState, useEffect, useRef } from 'react'
import {
  Briefcase, Gear, Brain, X, Check, Buildings, FileText
} from '@phosphor-icons/react'

import { Button } from '@/components/ui/button'
import ConfirmDialog from '@/components/shared/ConfirmDialog'

import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import JobDrawer from '@/components/jobs/drawer/JobDrawer'
import CompanyDrawer from '@/components/companies/CompanyDrawer'
import IntelligenceTab from '@/components/intelligence/IntelligenceTab'
import ResumeTab from '@/components/resume/ResumeTab'
import RulesTab from '@/components/rules/RulesTab'
import CompaniesPage from '@/components/companies/CompaniesPage'
import JobsPage from '@/components/jobs/JobsPage'
import WorkflowTerminal from '@/components/shared/WorkflowTerminal'
import DuplicateJobDialog from '@/components/shared/DuplicateJobDialog'

import { useJobs, usePending, useCompanies, useWorkflow, useToast, useIntelligence, useResume } from '@/hooks'

const API = '/api'

function App() {
  const { toast, showToast } = useToast()
  const { workflowDrawer, workflowLogs, workflowEndRef, openWorkflow, closeWorkflow } = useWorkflow()

  const {
    jobs, setJobs, summaries, setSummaries,
    jobsTotal, jobAgg, loadingMore,
    jobsScrollRef, jobsSentinelRef,
    sortBy, setSortBy, sortDir, setSortDir,
    filterCities, setFilterCities,
    filterCompanies, setFilterCompanies,
    filterTech, setFilterTech,
    filterMatches, setFilterMatches,
    filterWorkTypes, setFilterWorkTypes,
    filterEmploymentTypes, setFilterEmploymentTypes,
    filterResponseStatus, setFilterResponseStatus,
    filterApplied, setFilterApplied,
    activeFilterCount,
    allCities, allCompanies, filteredJobs,
    refreshJobs, loadMoreJobs, fetchJobs, fetchSummaries,
    deleteJob, requeueJob, rescoreJob, updateJob, clearFilters
  } = useJobs()

  const {
    pending, urlInput, setUrlInput, urlError, setUrlError,
    submitting, processImmediately, setProcessImmediately,
    duplicateJob, setDuplicateJob,
    fetchPending, submitUrl, deletePending, processPending, resetPending, pausePending
  } = usePending(refreshJobs)

  const {
    companies, pendingCompanies,
    fetchCompanies, fetchPendingCompanies,
    deleteCompany, reprocessCompany
  } = useCompanies()

  const {
    resumes, setResumes, linkedinProfiles,
    generatingResume, generatingCover,
    fetchResumes, fetchLinkedin, generateResume, generateCover
  } = useResume(showToast)

  const {
    analysis, timestamps, intelligenceSubTab, setIntelligenceSubTab, refreshing,
    fetchAnalysis, fetchTimestamps, getLastUpdated,
    refreshAnalysis, refreshStrategy, refreshNetworking,
    refreshSkills, refreshMarket, refreshOpportunity
  } = useIntelligence(refreshJobs)

  const [rules, setRules] = useState(null)
  const [tab, setTab] = useState(() => {
    const h = window.location.hash.replace('#', '') || 'jobs'
    return h.split('/')[0] || 'jobs'
  })
  const [deepLinkId, setDeepLinkId] = useState(() => {
    const h = window.location.hash.replace('#', '') || 'jobs'
    const parts = h.split('/')
    return parts[1] ? parseInt(parts[1]) : null
  })
  const [drawer, setDrawer] = useState(null)
  const [drawerTab, setDrawerTab] = useState('details')
  const [companyDrawer, setCompanyDrawer] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [confirmDialog, setConfirmDialog] = useState(null)
  const [collapsedSections, setCollapsedSections] = useState({})
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    Promise.all([fetchJobs(), fetchSummaries(), fetchResumes(), fetchLinkedin()])
    fetchPending()
    fetchRules()
    fetchAnalysis()
    fetchTimestamps()
    fetchCompanies()
    fetchPendingCompanies()
  }, [])

  const fetchRules = () => fetch(`${API}/rules`).then(r => r.json()).then(setRules)

  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace('#', '') || 'jobs'
      const parts = h.split('/')
      const newTab = parts[0] || 'jobs'
      const id = parts[1] ? parseInt(parts[1]) : null
      if (newTab && newTab !== tab) setTab(newTab)
      if (id) setDeepLinkId(id)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

  useEffect(() => {
    if (!deepLinkId) return
    if (tab === 'jobs' && jobs && !drawer) {
      openDrawer(deepLinkId)
      setDeepLinkId(null)
    }
  }, [deepLinkId, tab, jobs, drawer])

  useEffect(() => {
    const handleOpenJob = (e) => {
      const num = e.detail
      if (num && tab !== 'jobs') setTab('jobs')
      if (num) setTimeout(() => openDrawer(num), 100)
    }
    window.addEventListener('openJob', handleOpenJob)
    return () => window.removeEventListener('openJob', handleOpenJob)
  }, [tab, jobs])

  useEffect(() => {
    const sentinel = jobsSentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) loadMoreJobs()
    }, { threshold: 0.1 })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadMoreJobs])

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setConfirmDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  const handleDeleteJob = async (num) => {
    const ok = await showConfirm('Delete Job', `Permanently delete job #${num}? This cannot be undone.`, 'Delete Forever')
    if (!ok) return
    await deleteJob(num)
  }

  const handleRequeueJob = async (num) => {
    const ok = await showConfirm('Reprocess Job', `Reprocess job #${num} from scratch? The current version will be permanently deleted.`, 'Reprocess')
    if (!ok) return
    await requeueJob(num)
  }

  const handleUpdateJob = async (num, fields) => {
    const updated = await updateJob(num, fields)
    if (updated) {
      setDrawer(prev => prev && prev.job.num === num ? { ...prev, job: { ...prev.job, ...updated } } : prev)
    }
  }

  const openDrawer = async (num) => {
    if (!jobs) return
    const j = jobs.find(x => x.num === num)
    const s = summaries?.find(x => x.num === num)
    let fullJob = j
    try { const res = await fetch(`${API}/jobs/${num}`); if (res.ok) fullJob = await res.json() } catch {}
    const r = resumes?.find(x => x.job_num === num && !x.id.startsWith('cover_')) ||
              resumes?.find(x => !x.id.startsWith('original') && !x.id.startsWith('cover_') && fullJob.company.toLowerCase().includes((x.company || '').split(' ')[0].toLowerCase().replace(/[()]/g, '')))
    const cl = resumes?.find(x => x.job_num === num && x.id.startsWith('cover_'))
    setDrawer({ job: fullJob, summary: s, resume: r, coverLetter: cl })
    setDrawerTab('details')
    window.history.replaceState(null, '', `#jobs/${num}`)
  }

  const openCompanyDrawer = async (id) => {
    try {
      const res = await fetch(`${API}/companies/${id}`)
      const data = await res.json()
      setCompanyDrawer(data)
    } catch (e) {
      console.error('Failed to load company', e)
    }
  }

  const handleDeleteCompany = async (id) => {
    await deleteCompany(id)
    setCompanyDrawer(null)
  }

  const handleReprocessCompany = async (id) => {
    await reprocessCompany(id)
    setCompanyDrawer(null)
  }

  const switchTab = (t) => { setTab(t); setDeepLinkId(null); window.location.hash = t }

  const tabs = [
    { id: 'jobs', icon: <Briefcase className="w-4 h-4" />, label: 'Jobs', badge: jobsTotal, section: 'jobs' },
    { id: 'companies', icon: <Buildings className="w-4 h-4" />, label: 'Companies', badge: companies.length, section: 'jobs' },
    { id: 'resume', icon: <FileText className="w-4 h-4" />, label: 'Resume', section: 'jobs' },
    { id: 'intelligence', icon: <Brain className="w-4 h-4" />, label: 'Intelligence', section: 'analysis' },
    { id: 'rules', icon: <Gear className="w-4 h-4" />, label: 'Rules', section: 'settings' },
  ]

  if (jobs === null) return <div className="flex items-center justify-center h-screen text-muted-foreground">Loading...</div>

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Button variant="outline" size="icon" className="fixed top-3 left-3 z-[60] lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
      </Button>

      <Sidebar sidebarOpen={sidebarOpen} tabs={tabs} tab={tab} onSwitchTab={switchTab} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <Header jobAgg={jobAgg} jobsTotal={jobsTotal} resumes={resumes} companies={companies} theme={theme} tab={tab} onSwitchTab={switchTab} onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">
            {tab === 'jobs' && (
              <JobsPage
                pending={pending} jobs={jobs} filteredJobs={filteredJobs} jobsTotal={jobsTotal} filteredJobsCount={filteredJobs.length}
                urlInput={urlInput} setUrlInput={setUrlInput} urlError={urlError} setUrlError={setUrlError}
                submitting={submitting} processImmediately={processImmediately} setProcessImmediately={setProcessImmediately}
                sortBy={sortBy} setSortBy={setSortBy} sortDir={sortDir} setSortDir={setSortDir}
                filterTech={filterTech} setFilterTech={setFilterTech} filterCities={filterCities} setFilterCities={setFilterCities}
                filterCompanies={filterCompanies} setFilterCompanies={setFilterCompanies}
                filterMatches={filterMatches} setFilterMatches={setFilterMatches}
                filterWorkTypes={filterWorkTypes} setFilterWorkTypes={setFilterWorkTypes}
                filterEmploymentTypes={filterEmploymentTypes} setFilterEmploymentTypes={setFilterEmploymentTypes}
                filterResponseStatus={filterResponseStatus} setFilterResponseStatus={setFilterResponseStatus}
                filterApplied={filterApplied} setFilterApplied={setFilterApplied}
                allCities={allCities} allCompanies={allCompanies} activeFilterCount={activeFilterCount}
                collapsedSections={collapsedSections} setCollapsedSections={setCollapsedSections}
                loadingMore={loadingMore} jobsScrollRef={jobsScrollRef} jobsSentinelRef={jobsSentinelRef}
                submitUrl={submitUrl} deletePending={deletePending} processPending={processPending}
                resetPending={resetPending} pausePending={pausePending} openWorkflow={openWorkflow}
                rescoreJob={rescoreJob} deleteJob={handleDeleteJob} requeueJob={handleRequeueJob}
                openDrawer={openDrawer} refreshJobs={refreshJobs} clearFilters={clearFilters} loadMoreJobs={loadMoreJobs}
              />
            )}
            {tab === 'companies' && (
              <CompaniesPage companies={companies} pendingCompanies={pendingCompanies} deepLinkId={deepLinkId} onClearDeepLink={() => setDeepLinkId(null)} onRefresh={() => { fetchCompanies(); fetchPendingCompanies() }} onOpenJob={openDrawer} onNavigateToJob={(num) => { setTab('jobs'); setTimeout(() => openDrawer(num), 100) }} onOpenCompany={openCompanyDrawer} />
            )}
            {tab === 'intelligence' && (
              <IntelligenceTab analysis={analysis} timestamps={timestamps} getLastUpdated={getLastUpdated} jobs={jobs} resumes={resumes} linkedinProfiles={linkedinProfiles} cities={[]} rules={rules} intelligenceSubTab={intelligenceSubTab} refreshing={refreshing} onSetIntelligenceSubTab={setIntelligenceSubTab} onRefreshAll={refreshAnalysis} onRefreshMarket={refreshMarket} onRefreshOpportunity={refreshOpportunity} onRefreshStrategy={refreshStrategy} onRefreshNetworking={refreshNetworking} onRefreshSkills={refreshSkills} onOpenDrawer={openDrawer} />
            )}
            {tab === 'resume' && <ResumeTab resumes={resumes} linkedinProfiles={linkedinProfiles} onRefreshResumes={fetchResumes} onRefreshLinkedin={fetchLinkedin} />}
            {tab === 'rules' && <RulesTab rules={rules} onUpdate={fetchRules} />}
          </div>
        </div>
      </main>

      <JobDrawer drawer={drawer} drawerTab={drawerTab} generatingResume={generatingResume} generatingCover={generatingCover} companies={companies} onClose={() => { setDrawer(null); window.history.replaceState(null, '', '#jobs') }} onSetDrawerTab={setDrawerTab} onRescoreJob={rescoreJob} onRequeueJob={handleRequeueJob} onUpdateJob={handleUpdateJob} onSetToast={showToast} onGenerateResume={(num) => generateResume(num, setDrawer)} onGenerateCover={(num) => generateCover(num, setDrawer)} onLinkCompany={async (num, companyId) => { await fetch(`${API}/jobs/${num}/link-company`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ company_id: companyId }) }); const res = await fetch(`${API}/jobs/${num}`); const updated = await res.json(); setDrawer(prev => prev ? { ...prev, job: updated } : null) }} onOpenCompany={(id) => openCompanyDrawer(id)} onNavigateToCompany={(id) => { setTab('companies'); setTimeout(() => openCompanyDrawer(id), 100) }} />

      <CompanyDrawer
        company={companyDrawer}
        onClose={() => { setCompanyDrawer(null); window.history.replaceState(null, '', tab === 'companies' ? '#companies' : `#${tab}`) }}
        onDelete={handleDeleteCompany}
        onReprocess={handleReprocessCompany}
        onOpenJob={(num) => openDrawer(num)}
        onNavigateToJob={(num) => { setTab('jobs'); setTimeout(() => openDrawer(num), 100) }}
        onViewAllJobs={(companyName) => {
          setCompanyDrawer(null)
          setFilterCompanies([companyName])
          setTab('jobs')
          window.location.hash = 'jobs'
        }}
      />

      <ConfirmDialog dialog={confirmDialog} onClose={() => setConfirmDialog(null)} />

      <DuplicateJobDialog duplicateJob={duplicateJob} setDuplicateJob={setDuplicateJob}
        onRescore={async (num) => { await rescoreJob(num); fetchPending(); setDuplicateJob(null) }}
        onReprocess={async (num) => { await requeueJob(num); fetchPending(); setDuplicateJob(null) }} />

      <WorkflowTerminal workflowDrawer={workflowDrawer} workflowLogs={workflowLogs} workflowEndRef={workflowEndRef} onClose={closeWorkflow} />

      {toast && (
        <div className="fixed bottom-6 left-6 z-[300] px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all duration-300 bg-green-500">
          {toast}
        </div>
      )}
    </div>
  )
}

export default App
