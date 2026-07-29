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
    companies,
    fetchCompanies,
    deleteCompany,
    reprocessCompany,
  } = useCompanies();

  const {
    resumes,
    setResumes,
    linkedinProfiles,
    activeGens,
    generationResult,
    fetchResumes,
    fetchLinkedin,
    generateResume,
    generateCover,
    cancelGeneration,
  } = useResume();

  // Update drawer immediately when generation completes
  useEffect(() => {
    if (!generationResult) return
    const { type, content, content_id, job_num, title } = generationResult
    if (type === 'resume') {
      setDrawer(prev => prev ? { ...prev, resume: { id: content_id, content, job_num, title } } : null)
    } else if (type === 'cover') {
      setDrawer(prev => prev ? { ...prev, coverLetter: { id: content_id, content, job_num, title } } : null)
    }
  }, [generationResult])

  // Initialize insights sub-tab from hash for deep linking
  const [initialSubTab] = useState(() => {
    const h = window.location.hash.replace("#", "") || "";
    const parts = h.split("/");
    if (parts[0] === "insights" && parts[1] && !parseInt(parts[1])) {
      return parts[1];
    }
    return null;
  });

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
  } = useInsights(initialSubTab || undefined);

  const [rules, setRules] = useState(null);
  const [tab, setTab] = useState(() => {
    const h = window.location.hash.replace("#", "") || "jobs";
    return h.split("/")[0] || "jobs";
  });
  const [deepLinkId, setDeepLinkId] = useState(() => {
    const h = window.location.hash.replace("#", "") || "jobs";
    const parts = h.split("/");
    if (parts[0] === "companies" && parts[1]) return null;
    return parts[1] ? parseInt(parts[1]) : null;
  });
  const [deepLinkCompanyId, setDeepLinkCompanyId] = useState<string | null>(() => {
    const h = window.location.hash.replace("#", "") || "";
    const parts = h.split("/");
    if (parts[0] === "companies" && parts[1]) return parts[1];
    return null;
  });
  const [deepLinkSkill, setDeepLinkSkill] = useState<string | null>(() => {
    const h = window.location.hash.replace("#", "") || "";
    const parts = h.split("/");
    // #skills/Kafka or #insights/skills/Kafka
    if ((parts[0] === "skills" || parts[0] === "insights") && parts[1] && isNaN(parseInt(parts[1]))) {
      return decodeURIComponent(parts[1]);
    }
    if (parts[0] === "insights" && parts[2] && isNaN(parseInt(parts[2]))) {
      return decodeURIComponent(parts[2]);
    }
    return null;
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
    fetchRules();
    fetchCompanies();
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
        // #insights/skills/Kafka — skill name in third segment
        const third = parts[2] || null;
        if (second === "skills" && third && isNaN(parseInt(third))) {
          setDeepLinkSkill(decodeURIComponent(third));
        }
      } else if (newTab === "skills" && second && isNaN(parseInt(second))) {
        // #skills/Kafka — skill name in second segment
        setDeepLinkSkill(decodeURIComponent(second));
      } else if (newTab === "companies" && second) {
        // #companies/{id} — company drawer
        setDeepLinkCompanyId(second);
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
    if (!deepLinkCompanyId) return;
    if (tab === "companies" && !companyDrawer) {
      openCompanyDrawer(deepLinkCompanyId);
      setDeepLinkCompanyId(null);
    }
  }, [deepLinkCompanyId, tab, companyDrawer]);

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
    setDrawer({
      job: fullJob,
      summary: s,
      resume: fullJob.resume || null,
      coverLetter: fullJob.coverLetter || null,
    });
    setDrawerTab("details");
    window.history.replaceState(null, "", `#jobs/${num}`);
  };

  const openCompanyDrawer = async (id) => {
    try {
      const res = await fetch(`${API}/companies/${id}`);
      const data = await res.json();
      setCompanyDrawer(data);
      window.history.replaceState(null, "", `#companies/${id}`);
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
      id: "skills",
      icon: <TreeStructure className="w-4 h-4" />,
      label: "Skills",
      section: "jobs",
    },
    {
      id: "insights",
      icon: <Lightbulb className="w-4 h-4" />,
      label: "Insights",
      section: "jobs",
      children: [
        { id: "overview", label: "Overview" },
        { id: "skills", label: "Skills" },
        { id: "opportunities", label: "Opportunities" },
        { id: "companies", label: "Companies" },
        { id: "market", label: "Market" },
        { id: "networking", label: "Networking" },
      ],
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
                jobs={jobs}
                filteredJobs={filteredJobs}
                jobsTotal={jobsTotal}
                filteredJobsCount={filteredJobs.length}
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
                loadingMore={loadingMore}
                jobsScrollRef={jobsScrollRef}
                jobsSentinelRef={jobsSentinelRef}
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
                deepLinkId={deepLinkCompanyId}
                onClearDeepLink={() => setDeepLinkCompanyId(null)}
                onRefresh={() => {
                  fetchCompanies();
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
              <SkillsTab deepLinkSkill={deepLinkSkill} onClearDeepLink={() => setDeepLinkSkill(null)} />
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
        activeGens={activeGens}
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
        onGenerateResume={(num) => generateResume(num)}
        onGenerateCover={(num) => generateCover(num)}
        onCancelGeneration={cancelGeneration}
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
        duplicateJob={null}
        setDuplicateJob={() => {}}
        onRescore={async (num) => {
          await rescoreJob(num);
          setDuplicateJob(null);
        }}
        onReprocess={async (num) => {
          await requeueJob(num);
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
