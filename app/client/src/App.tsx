import { useState, useEffect, useRef, useCallback } from "react";
import {
  Briefcase,
  Gear,
  Brain,
  X,
  Check,
  Buildings,
  FileText,
  Lightbulb,
  Spinner,
  TreeStructure,
} from "@phosphor-icons/react";
import { ThemeProvider } from "next-themes";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Toaster } from "@/shared/ui/sonner";
import { Progress } from "@/shared/ui/progress";
import ConfirmDialog from "@/shared/components/ConfirmDialog";

import Sidebar from "@/layout/Sidebar";
import Header from "@/layout/Header";
import JobDrawer from "@/features/jobs/components/drawer/JobDrawer";
import CompanyDrawer from "@/features/companies/components/CompanyDrawer";
import InsightsTab from "@/features/insights/components/InsightsTab";
import SkillsTab from "@/features/skills/components/SkillsTab";
import ResumeTab from "@/features/resume/components/ResumeTab";
import RulesTab from "@/features/rules/components/RulesTab";
import CompaniesPage from "@/features/companies/components/CompaniesPage";
import JobsPage from "@/features/jobs/components/JobsPage";
import WorkflowTerminal from "@/shared/components/WorkflowTerminal";
import DuplicateJobDialog from "@/shared/components/DuplicateJobDialog";

import {
  useJobs,
  usePending,
  useCompanies,
  useWorkflow,
  useResume,
  useInsights,
} from "@/shared/hooks";
import { useSocketIO } from "@/shared/hooks/useSocketIO";

const API = "/api";

function App() {
  const {
    workflowDrawer,
    workflowLogs,
    workflowEndRef,
    openWorkflow,
    closeWorkflow,
  } = useWorkflow();

  const {
    jobs,
    setJobs,
    summaries,
    setSummaries,
    jobsTotal,
    jobAgg,
    loadingMore,
    jobsScrollRef,
    jobsSentinelRef,
    sortBy,
    setSortBy,
    sortDir,
    setSortDir,
    filterCities,
    setFilterCities,
    filterCompanies,
    setFilterCompanies,
    filterTech,
    setFilterTech,
    filterMatches,
    setFilterMatches,
    filterWorkTypes,
    setFilterWorkTypes,
    filterEmploymentTypes,
    setFilterEmploymentTypes,
    filterResponseStatus,
    setFilterResponseStatus,
    filterApplied,
    setFilterApplied,
    filterScores,
    setFilterScores,
    activeFilterCount,
    allCities,
    allCompanies,
    filteredJobs,
    refreshJobs,
    loadMoreJobs,
    fetchJobs,
    fetchSummaries,
    deleteJob,
    requeueJob,
    rescoreJob,
    updateJob,
    clearFilters,
  } = useJobs();

  const {
    pending,
    urlInput,
    setUrlInput,
    urlError,
    setUrlError,
    submitting,
    processImmediately,
    setProcessImmediately,
    duplicateJob,
    setDuplicateJob,
    fetchPending,
    submitUrl,
    deletePending,
    processPending,
    resetPending,
    pausePending,
  } = usePending(refreshJobs);

  const {
    companies,
    pendingCompanies,
    fetchCompanies,
    fetchPendingCompanies,
    deleteCompany,
    reprocessCompany,
  } = useCompanies();

  const {
    resumes,
    setResumes,
    linkedinProfiles,
    generatingResume,
    generatingCover,
    fetchResumes,
    fetchLinkedin,
    generateResume,
    generateCover,
  } = useResume();

  const {
    data: careerData,
    status: careerStatus,
    progress: careerProgress,
    activeTab: careerSubTab,
    setActiveTab: setCareerSubTab,
    refreshing: careerRefreshing,
    error: careerError,
    fetchData: fetchCareerData,
    fetchStatus: fetchCareerStatus,
    fetchProgress: fetchCareerProgress,
    refreshSection: refreshCareerSection,
    refreshAll: refreshCareerAll,
    cancelRun: cancelCareerRun,
  } = useInsights();

  const [rules, setRules] = useState(null);
  const [tab, setTab] = useState(() => {
    const h = window.location.hash.replace("#", "") || "jobs";
    return h.split("/")[0] || "jobs";
  });
  const [deepLinkId, setDeepLinkId] = useState(() => {
    const h = window.location.hash.replace("#", "") || "jobs";
    const parts = h.split("/");
    return parts[1] ? parseInt(parts[1]) : null;
  });
  const [drawer, setDrawer] = useState(null);
  const [drawerTab, setDrawerTab] = useState("details");
  const [companyDrawer, setCompanyDrawer] = useState(null);
  const [theme, setTheme] = useState(
    () => localStorage.getItem("theme") || "dark",
  );
  const [confirmDialog, setConfirmDialog] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const socket = useSocketIO();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    Promise.all([
      fetchJobs(),
      fetchSummaries(),
      fetchResumes(),
      fetchLinkedin(),
    ]);
    fetchPending();
    fetchRules();
    fetchCompanies();
    fetchPendingCompanies();
    fetchCareerData();
    fetchCareerStatus();
    fetchCareerProgress();
  }, []);

  const fetchRules = () =>
    fetch(`${API}/rules`)
      .then((r) => r.json())
      .then(setRules);

  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace("#", "") || "jobs";
      const parts = h.split("/");
      const newTab = parts[0] || "jobs";
      const second = parts[1] || null;
      if (newTab && newTab !== tab) setTab(newTab);
      // For insights, second part is sub-tab (e.g. #insights/skills)
      if (newTab === "insights" && second && !parseInt(second)) {
        setCareerSubTab(second);
      } else if (second) {
        setDeepLinkId(parseInt(second));
      }
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [tab]);

  useEffect(() => {
    if (!deepLinkId) return;
    if (tab === "jobs" && jobs && !drawer) {
      openDrawer(deepLinkId);
      setDeepLinkId(null);
    }
  }, [deepLinkId, tab, jobs, drawer]);

  useEffect(() => {
    const handleOpenJob = (e) => {
      const num = e.detail;
      if (num && tab !== "jobs") setTab("jobs");
      if (num) setTimeout(() => openDrawer(num), 100);
    };
    window.addEventListener("openJob", handleOpenJob);
    return () => window.removeEventListener("openJob", handleOpenJob);
  }, [tab, jobs]);

  useEffect(() => {
    const sentinel = jobsSentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) loadMoreJobs();
      },
      { threshold: 0.1 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMoreJobs]);

  const showConfirm = (title, message, confirmLabel, variant = "danger") => {
    return new Promise((resolve) => {
      setConfirmDialog({ title, message, confirmLabel, variant, resolve });
    });
  };

  const handleDeleteJob = async (num) => {
    const ok = await showConfirm(
      "Delete Job",
      `Permanently delete job #${num}? This cannot be undone.`,
      "Delete Forever",
    );
    if (!ok) return;
    await deleteJob(num);
  };

  const handleRequeueJob = async (num) => {
    const ok = await showConfirm(
      "Reprocess Job",
      `Reprocess job #${num} from scratch? The current version will be permanently deleted.`,
      "Reprocess",
    );
    if (!ok) return;
    await requeueJob(num);
  };

  const handleUpdateJob = async (num, fields) => {
    const updated = await updateJob(num, fields);
    if (updated) {
      setDrawer((prev) =>
        prev && prev.job.num === num
          ? { ...prev, job: { ...prev.job, ...updated } }
          : prev,
      );
    }
  };

  const openDrawer = async (num) => {
    if (!jobs) return;
    const j = jobs.find((x) => x.num === num);
    const s = summaries?.find((x) => x.num === num);
    let fullJob = j;
    try {
      const res = await fetch(`${API}/jobs/${num}`);
      if (res.ok) fullJob = await res.json();
    } catch {}
    const r =
      resumes?.find((x) => x.job_num === num && !x.id.startsWith("cover_")) ||
      resumes?.find(
        (x) =>
          !x.id.startsWith("original") &&
          !x.id.startsWith("cover_") &&
          fullJob.company
            .toLowerCase()
            .includes(
              (x.company || "")
                .split(" ")[0]
                .toLowerCase()
                .replace(/[()]/g, ""),
            ),
      );
    const cl = resumes?.find(
      (x) => x.job_num === num && x.id.startsWith("cover_"),
    );
    setDrawer({ job: fullJob, summary: s, resume: r, coverLetter: cl });
    setDrawerTab("details");
    window.history.replaceState(null, "", `#jobs/${num}`);
  };

  const openCompanyDrawer = async (id) => {
    try {
      const res = await fetch(`${API}/companies/${id}`);
      const data = await res.json();
      setCompanyDrawer(data);
    } catch (e) {
      console.error("Failed to load company", e);
    }
  };

  // Navigate to Companies page to add a new company
  const handleAddCompany = (companyName) => {
    setTab("companies");
    window.location.hash = "companies";
    // The CompaniesPage has an add flow triggered via pending companies
  };

  const handleDeleteCompany = async (id) => {
    await deleteCompany(id);
    setCompanyDrawer(null);
  };

  const handleReprocessCompany = async (id) => {
    await reprocessCompany(id);
    setCompanyDrawer(null);
  };

  const switchTab = (t, sub) => {
    setTab(t);
    setDeepLinkId(null);
    if (sub) {
      setCareerSubTab(sub);
      window.location.hash = `${t}/${sub}`;
    } else {
      window.location.hash = t;
    }
  };

  const tabs = [
    {
      id: "jobs",
      icon: <Briefcase className="w-4 h-4" />,
      label: "Jobs",
      badge: jobsTotal,
      section: "jobs",
    },
    {
      id: "companies",
      icon: <Buildings className="w-4 h-4" />,
      label: "Companies",
      badge: companies.length,
      section: "jobs",
    },
    {
      id: "insights",
      icon: <Lightbulb className="w-4 h-4" />,
      label: "Insights",
      section: "insights",
      children: [
        { id: "overview", label: "Overview" },
        { id: "opportunities", label: "Opportunities" },
        { id: "companies", label: "Companies" },
        { id: "market", label: "Market" },
        { id: "networking", label: "Networking" },
      ],
    },
    {
      id: "skills",
      icon: <Brain className="w-4 h-4" />,
      label: "Skills",
      section: "growth hub",
    },
    {
      id: "resume",
      icon: <FileText className="w-4 h-4" />,
      label: "Resume",
      section: "settings",
    },
    {
      id: "rules",
      icon: <Gear className="w-4 h-4" />,
      label: "Rules",
      section: "settings",
    },
  ];

  if (jobs === null)
    return (
      <div className="flex items-center justify-center h-screen text-muted-foreground">
        Loading...
      </div>
    );

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Button
        variant="outline"
        size="icon"
        className="fixed top-3 left-3 z-[60] lg:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? (
          <X className="w-4 h-4" />
        ) : (
          <Check className="w-4 h-4" />
        )}
      </Button>

      <Sidebar
        sidebarOpen={sidebarOpen}
        tabs={tabs}
        tab={tab}
        onSwitchTab={switchTab}
        subTab={careerSubTab}
        onSwitchSubTab={setCareerSubTab}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <Header
          jobAgg={jobAgg}
          jobsTotal={jobsTotal}
          resumes={resumes}
          companies={companies}
          theme={theme}
          tab={tab}
          onSwitchTab={switchTab}
          onToggleTheme={() =>
            setTheme((t) => (t === "dark" ? "light" : "dark"))
          }
        />

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">
            {tab === "jobs" && (
              <JobsPage
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
                pausePending={pausePending}
                openWorkflow={openWorkflow}
                rescoreJob={rescoreJob}
                deleteJob={handleDeleteJob}
                requeueJob={handleRequeueJob}
                openDrawer={openDrawer}
                refreshJobs={refreshJobs}
                clearFilters={clearFilters}
                loadMoreJobs={loadMoreJobs}
                onOpenCompany={openCompanyDrawer}
              />
            )}
            {tab === "companies" && (
              <CompaniesPage
                companies={companies}
                pendingCompanies={pendingCompanies}
                deepLinkId={deepLinkId}
                onClearDeepLink={() => setDeepLinkId(null)}
                onRefresh={() => {
                  fetchCompanies();
                  fetchPendingCompanies();
                }}
                onOpenJob={openDrawer}
                onNavigateToJob={(num) => {
                  setTab("jobs");
                  setTimeout(() => openDrawer(num), 100);
                }}
                onOpenCompany={openCompanyDrawer}
              />
            )}
            {tab === "insights" && (
              <InsightsTab
                data={careerData}
                status={careerStatus}
                progress={careerProgress}
                activeTab={careerSubTab}
                setActiveTab={setCareerSubTab}
                refreshing={careerRefreshing}
                error={careerError}
                onRefreshAll={refreshCareerAll}
                onRefreshSection={refreshCareerSection}
                onOpenDrawer={openDrawer}
                onOpenCompany={openCompanyDrawer}
                onAddCompany={handleAddCompany}
                onCancel={cancelCareerRun}
              />
            )}
            {tab === "skills" && (
              <SkillsTab />
            )}
            {tab === "resume" && (
              <ResumeTab
                resumes={resumes}
                linkedinProfiles={linkedinProfiles}
                onRefreshResumes={fetchResumes}
                onRefreshLinkedin={fetchLinkedin}
              />
            )}
            {tab === "rules" && (
              <RulesTab rules={rules} onUpdate={fetchRules} />
            )}
          </div>
        </div>
      </main>

      <JobDrawer
        drawer={drawer}
        drawerTab={drawerTab}
        generatingResume={generatingResume}
        generatingCover={generatingCover}
        companies={companies}
        onClose={() => {
          setDrawer(null);
          window.history.replaceState(null, "", "#jobs");
        }}
        onSetDrawerTab={setDrawerTab}
        onRescoreJob={rescoreJob}
        onRequeueJob={handleRequeueJob}
        onUpdateJob={handleUpdateJob}
        onSetToast={(msg) => toast.success(msg)}
        onGenerateResume={(num) => generateResume(num, setDrawer)}
        onGenerateCover={(num) => generateCover(num, setDrawer)}
        onLinkCompany={async (num, companyId) => {
          await fetch(`${API}/jobs/${num}/link-company`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ company_id: companyId }),
          });
          const res = await fetch(`${API}/jobs/${num}`);
          const updated = await res.json();
          setDrawer((prev) => (prev ? { ...prev, job: updated } : null));
        }}
        onOpenCompany={(id) => openCompanyDrawer(id)}
        onNavigateToCompany={(id) => {
          setTab("companies");
          setTimeout(() => openCompanyDrawer(id), 100);
        }}
      />

      <CompanyDrawer
        company={companyDrawer}
        onClose={() => {
          setCompanyDrawer(null);
          window.history.replaceState(
            null,
            "",
            tab === "companies" ? "#companies" : `#${tab}`,
          );
        }}
        onDelete={handleDeleteCompany}
        onReprocess={handleReprocessCompany}
        onOpenJob={(num) => openDrawer(num)}
        onNavigateToJob={(num) => {
          setTab("jobs");
          setTimeout(() => openDrawer(num), 100);
        }}
        onViewAllJobs={(companyName) => {
          setCompanyDrawer(null);
          setFilterCompanies([companyName]);
          setTab("jobs");
          window.location.hash = "jobs";
        }}
      />

      <ConfirmDialog
        dialog={confirmDialog}
        onClose={() => setConfirmDialog(null)}
      />

      <DuplicateJobDialog
        duplicateJob={duplicateJob}
        setDuplicateJob={setDuplicateJob}
        onRescore={async (num) => {
          await rescoreJob(num);
          fetchPending();
          setDuplicateJob(null);
        }}
        onReprocess={async (num) => {
          await requeueJob(num);
          fetchPending();
          setDuplicateJob(null);
        }}
      />

      <WorkflowTerminal
        workflowDrawer={workflowDrawer}
        workflowLogs={workflowLogs}
        workflowEndRef={workflowEndRef}
        onClose={closeWorkflow}
      />

      <Toaster />
    </div>
  );
}

export default function AppWithTheme() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <App />
    </ThemeProvider>
  );
}
