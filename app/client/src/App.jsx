import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  Briefcase, ChartBar, Gear, Target, Brain, Sun, Moon,
  Clock, X, CheckCircle, MagnifyingGlass, Buildings, ArrowsClockwise,
  Rocket, IdentificationCard, FileText, Link, Globe, Clipboard,
  Lightning, TrendUp, BookOpen, ChartLineUp, Wrench, Warning,
  Confetti, FloppyDisk, House, Pause, Trash, Repeat, PencilSimple,
  Users, Spinner, Stack, Check, CaretDown, Keyboard,
  ListChecks, Star, Gift, Shield, MapPin, TreePalm, MusicNote, Bank, Factory,
  HouseSimple, Bug, Compass, ArrowRight,
  CurrencyDollar, UsersFour, HourglassHigh, Handshake, Student, Lightbulb, GraduationCap, Copy,
  LinkedinLogo
} from '@phosphor-icons/react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from '@/components/ui/alert-dialog'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

import ProcessingItem from '@/components/ProcessingItem'
import { CompactJobCard, JobCard, CITY_COLORS, DEFAULT_CITY_COLOR, VISA_STYLES, getScoreColor, getMatchClass, LocationBadge, VisaBadge, WorkTypeTag, scoreRank } from '@/components/ProcessedCards'
import { TechCard, StackCard } from '@/components/TechCards'
import ResumeTab from '@/components/ResumeTab'
import ResumePreview from '@/components/ResumePreview'
import RulesTab from '@/components/RulesTab'
import { MultiSelect } from '@/components/MultiSelect'

const API = '/api'

const EMOJI_ICON_MAP = {
  '🎯': <Target className="w-4 h-4" />,
  '🌍': <Globe className="w-4 h-4" />,
  '⚡': <Lightning className="w-4 h-4" />,
  '🏢': <Buildings className="w-4 h-4" />,
  '🐍': <Bug className="w-4 h-4" />,
  '📋': <Clipboard className="w-4 h-4" />,
  '🚀': <Rocket className="w-4 h-4" />,
  '🔗': <Link className="w-4 h-4" />,
  '📈': <TrendUp className="w-4 h-4" />,
  '💪': <TrendUp className="w-4 h-4" />,
  '📚': <BookOpen className="w-4 h-4" />,
  '💡': <Lightbulb className="w-4 h-4" />,
  '🐻': <TreePalm className="w-4 h-4" />,
  '🦁': <Compass className="w-4 h-4" />,
  '🎵': <MusicNote className="w-4 h-4" />,
  '🏛️': <Buildings className="w-4 h-4" />,
  '🏦': <Bank className="w-4 h-4" />,
  '🗼': <Buildings className="w-4 h-4" />,
  '🏭': <Factory className="w-4 h-4" />,
  '🏠': <HouseSimple className="w-4 h-4" />,
  '🇩🇪': <Globe className="w-4 h-4" />,
  '📍': <MapPin className="w-4 h-4" />,
  '💼': <Briefcase className="w-4 h-4" />,
  '🛂': <IdentificationCard className="w-4 h-4" />,
  '📊': <ChartBar className="w-4 h-4" />,
  '🔧': <Wrench className="w-4 h-4" />,
  '🔍': <MagnifyingGlass className="w-4 h-4" />,
  '🧠': <Brain className="w-4 h-4" />,
  '⚙️': <Gear className="w-4 h-4" />,
  '🎓': <GraduationCap className="w-4 h-4" />,
  '💰': <CurrencyDollar className="w-4 h-4" />,
  '👥': <Users className="w-4 h-4" />,
  '⏳': <HourglassHigh className="w-4 h-4" />,
  '🤝': <Handshake className="w-4 h-4" />,
}

function EmojiIcon({ emoji }) {
  return EMOJI_ICON_MAP[emoji] || <span className="w-4 h-4">{emoji}</span>
}

function App() {
  const [jobs, setJobs] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [resumes, setResumes] = useState([])
  const [linkedinProfiles, setLinkedinProfiles] = useState([])
  const [cities, setCities] = useState([])
  const [tab, setTab] = useState(() => window.location.hash.replace('#', '') || 'jobs')
  const [drawer, setDrawer] = useState(null)
  const [drawerTab, setDrawerTab] = useState('details')
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [pending, setPending] = useState([])
  const [urlInput, setUrlInput] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [processImmediately, setProcessImmediately] = useState(true)
  const [urlError, setUrlError] = useState('')
  const [duplicateJob, setDuplicateJob] = useState(null)
  const [toast, setToast] = useState(null)
  const [confirmDialog, setConfirmDialog] = useState(null)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [filterCities, setFilterCities] = useState([])
  const [filterCompanies, setFilterCompanies] = useState([])
  const [filterTech, setFilterTech] = useState('')
  const [filterMatches, setFilterMatches] = useState([])
  const [filterWorkTypes, setFilterWorkTypes] = useState([])
  const [filterEmploymentTypes, setFilterEmploymentTypes] = useState([])
  const [collapsedSections, setCollapsedSections] = useState({})
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [dragOverCol, setDragOverCol] = useState(null)
  const JOBS_PAGE_SIZE = 30
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobAgg, setJobAgg] = useState({ total: 0, high_match: 0, apply_now: 0, remote: 0 })
  const [loadingMore, setLoadingMore] = useState(false)
  const jobsScrollRef = useRef(null)
  const jobsSentinelRef = useRef(null)
  const [dragId, setDragId] = useState(null)
  const [workflowDrawer, setWorkflowDrawer] = useState(null)
  const [workflowLogs, setWorkflowLogs] = useState([])
  const workflowWs = useRef(null)
  const workflowEndRef = useRef(null)
  const [rules, setRules] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [dashboardSubTab, setDashboardSubTab] = useState('overview')
  const [refreshing, setRefreshing] = useState({})

  // Toast listener
  useEffect(() => {
    const handler = (e) => { setToast(e.detail); setTimeout(() => setToast(null), 2000) }
    window.addEventListener('toast', handler)
    return () => window.removeEventListener('toast', handler)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    Promise.all([
      fetch(`${API}/jobs?offset=0&limit=${JOBS_PAGE_SIZE}&sort_by=created_at&sort_dir=desc`).then(r => r.json()),
      fetch(`${API}/summaries`).then(r => r.json()),
      fetch(`${API}/resumes`).then(r => r.json()),
      fetch(`${API}/linkedin`).then(r => r.json()),
      fetch(`${API}/cities`).then(r => r.json()),
    ]).then(([jobsData, sums, res, linkedin, cits]) => {
      setJobs(jobsData.jobs || []); setJobsTotal(jobsData.total || 0); setJobAgg(jobsData.agg || {}); setJobsPage(0)
      setSummaries(sums); setResumes(res); setLinkedinProfiles(linkedin); setCities(cits)
    })
    fetchPending(); fetchRules(); fetchAnalysis()
  }, [])

  const fetchRules = () => fetch(`${API}/rules`).then(r => r.json()).then(setRules)
  const fetchAnalysis = () => fetch(`${API}/analysis`).then(r => r.ok ? r.json() : null).then(data => setAnalysis(data)).catch(() => setAnalysis(null))

  const seenDoneRef = useRef(new Set())
  const refreshJobs = () => {
    setJobsPage(0)
    const params = new URLSearchParams()
    params.set('offset', '0'); params.set('limit', String(JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => { setJobs(d.jobs || []); setJobsTotal(d.total || 0); setJobAgg(d.agg || {}) })
  }

  const loadMoreJobs = useCallback(async () => {
    if (loadingMore) return
    const nextPage = jobsPage + 1; const offset = nextPage * JOBS_PAGE_SIZE
    if (offset >= jobsTotal) return
    setLoadingMore(true)
    try {
      const params = new URLSearchParams()
      params.set('offset', String(offset)); params.set('limit', String(JOBS_PAGE_SIZE))
      params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
      if (filterCities.length) params.set('filter_cities', filterCities.join(','))
      if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
      if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
      if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
      if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
      if (filterTech) params.set('filter_tech', filterTech)
      const res = await fetch(`${API}/jobs?${params}`); const data = await res.json()
      setJobs(prev => [...prev, ...(data.jobs || [])]); setJobsPage(nextPage)
    } finally { setLoadingMore(false) }
  }, [jobsPage, jobsTotal, loadingMore, sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech])

  useEffect(() => {
    let es
    const checkDone = (pendingList) => {
      const newlyDone = pendingList.filter(p => p.status === 'done' && !seenDoneRef.current.has(p.id))
      if (newlyDone.length > 0) { newlyDone.forEach(p => seenDoneRef.current.add(p.id)); refreshJobs() }
    }
    const connect = () => {
      es = new EventSource(`${API}/pending/stream`)
      es.onmessage = (e) => { try { const list = JSON.parse(e.data); setPending(list); checkDone(list) } catch {} }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    const poll = setInterval(() => { fetchPending().then(checkDone); refreshJobs() }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech])

  useEffect(() => {
    const onHash = () => { const h = window.location.hash.replace('#', ''); if (h && h !== tab) setTab(h) }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

  useEffect(() => {
    const sentinel = jobsSentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMoreJobs() }, { threshold: 0.1 })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadMoreJobs])

  const fetchPending = () => fetch(`${API}/pending`).then(r => r.json()).then(list => { setPending(list); return list })

  const submitUrl = async () => {
    if (!urlInput.trim()) return; setUrlError(''); setSubmitting(true)
    const res = await fetch(`${API}/pending`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: urlInput.trim(), source: 'web' }) })
    const data = await res.json()
    if (res.ok && data.status === 'exists') { setDuplicateJob(data); setUrlInput(''); setSubmitting(false); return }
    if (!res.ok) { setUrlError(data.error || 'Failed to add URL'); setSubmitting(false); return }
    setUrlInput(''); setSubmitting(false); fetchPending()
    if (processImmediately && data.id) await processPending(data.id)
  }

  const deletePending = async (id) => { await fetch(`${API}/pending/${id}`, { method: 'DELETE' }); fetchPending() }
  const processPending = async (id) => { await fetch(`${API}/pending/${id}/process`, { method: 'POST' }); fetchPending() }
  const resetPending = async (id) => { await fetch(`${API}/pending/${id}/reset`, { method: 'PUT' }); fetchPending() }
  const pausePending = async (id) => { await fetch(`${API}/pending/${id}/pause`, { method: 'PUT' }); fetchPending() }
  const rescoreJob = async (num) => { await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs() }
  const rescoreAll = async () => { await fetch(`${API}/jobs/rescore-all`, { method: 'POST' }); fetchPending(); refreshJobs() }

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setConfirmDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  const reprocessAll = async () => {
    const ok = await showConfirm('Reprocess All', 'Reprocess ALL jobs? Every job will be re-queued for full processing from scratch.', 'Reprocess All')
    if (!ok) return; await fetch(`${API}/jobs/reprocess-all`, { method: 'POST' }); fetchPending()
  }

  const deleteJob = async (num) => {
    const ok = await showConfirm('Delete Job', `Permanently delete job #${num}? This cannot be undone.`, 'Delete Forever')
    if (!ok) return; await fetch(`${API}/jobs/${num}`, { method: 'DELETE' }); refreshJobs()
  }

  const requeueJob = async (num) => {
    const ok = await showConfirm('Reprocess Job', `Reprocess job #${num} from scratch? The current version will be permanently deleted.`, 'Reprocess')
    if (!ok) return; await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' }); fetchPending(); refreshJobs()
  }

  const connectWorkflowWs = (pid) => {
    if (workflowWs.current) workflowWs.current.close()
    const ws = new WebSocket(`ws://${window.location.hostname}:8765`)
    workflowWs.current = ws
    ws.onopen = () => { ws.send(JSON.stringify({ action: 'watch', pid })) }
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt.type === 'state') { setWorkflowLogs(evt.logs || []) }
        else if (evt.type === 'tool_output') {
          const { stream, tool, data } = evt
          if (stream === 'input') setWorkflowLogs(prev => [...prev, { step: 'cmd', msg: data, ts: evt.ts }])
          else if (stream === 'output') data.split('\n').forEach(line => { if (line.trim()) setWorkflowLogs(prev => [...prev, { step: 'out', msg: line, ts: evt.ts }]) })
          else if (stream === 'error') setWorkflowLogs(prev => [...prev, { step: 'err', msg: data, ts: evt.ts }])
          else if (stream === 'text') setWorkflowLogs(prev => [...prev, { step: 'mimo', msg: data, ts: evt.ts }])
        }
        else if (evt.type === 'mimo_event' && evt.event?.type === 'step_finish') {
          const reason = evt.event.part?.reason || ''; const tokens = evt.event.part?.tokens?.total || 0
          setWorkflowLogs(prev => [...prev, { step: 'step', msg: `Step finished: ${reason} (${tokens} tokens)`, ts: evt.ts }])
        }
        else if (evt.type === 'mimo_raw') setWorkflowLogs(prev => [...prev, { step: 'raw', msg: evt.line, ts: evt.ts }])
        else if (evt.type === 'job_info') setPending(prev => prev.map(p => p.id === evt.pid ? { ...p, company: evt.company || p.company, title: evt.title } : p))
        else if (evt.type === 'step') setWorkflowLogs(prev => [...prev, { step: evt.step, msg: `[${evt.status}]`, ts: evt.ts }])
        else if (evt.type === 'complete') setWorkflowLogs(prev => [...prev, { step: 'done', msg: `Complete: ${evt.company} #${evt.num}`, ts: evt.ts }])
        else if (evt.type === 'error') setWorkflowLogs(prev => [...prev, { step: 'error', msg: evt.msg, ts: evt.ts }])
      } catch {}
    }
  }

  useEffect(() => { workflowEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [workflowLogs])

  const openWorkflow = (item) => { setWorkflowLogs([]); setWorkflowDrawer(item); connectWorkflowWs(item.id) }

  const jobsWithLocations = useMemo(() => {
    if (!jobs) return []
    return jobs.map(j => {
      let locations = []
      if (j.locations) { try { locations = typeof j.locations === 'string' ? JSON.parse(j.locations) : j.locations } catch { locations = [] } }
      if (!locations.length && j.location) locations = [j.location]
      return { ...j, parsedLocations: locations }
    })
  }, [jobs])

  const allCities = jobsWithLocations ? [...new Set(jobsWithLocations.flatMap(j => j.parsedLocations))].sort() : []
  const allCompanies = jobsWithLocations ? [...new Set(jobsWithLocations.map(j => j.company))].sort() : []

  const filteredJobs = useMemo(() => {
    if (!jobsWithLocations) return []
    let r = [...jobsWithLocations]
    r.sort((a, b) => {
      if (sortBy === 'score') {
        // Fit primary, success as tiebreaker
        const fitDiff = scoreRank(b.score) - scoreRank(a.score)
        if (fitDiff !== 0) return sortDir === 'desc' ? fitDiff : -fitDiff
        return sortDir === 'desc' ? scoreRank(b.success) - scoreRank(a.success) : scoreRank(a.success) - scoreRank(b.success)
      }
      if (sortBy === 'score_success') {
        // Success primary, fit as tiebreaker
        const successDiff = scoreRank(b.success) - scoreRank(a.success)
        if (successDiff !== 0) return sortDir === 'desc' ? successDiff : -successDiff
        return sortDir === 'desc' ? scoreRank(b.score) - scoreRank(a.score) : scoreRank(a.score) - scoreRank(b.score)
      }
      if (sortBy === 'score_combined') {
        // Combined sum of both scores
        return sortDir === 'desc' ? (scoreRank(b.score) + scoreRank(b.success)) - (scoreRank(a.score) + scoreRank(a.success)) : (scoreRank(a.score) + scoreRank(a.success)) - (scoreRank(b.score) + scoreRank(b.success))
      }
      if (sortBy === 'num') return sortDir === 'desc' ? b.num - a.num : a.num - b.num
      if (sortBy === 'company') return sortDir === 'desc' ? b.company.localeCompare(a.company) : a.company.localeCompare(b.company)
      if (sortBy === 'location') return sortDir === 'desc' ? b.location.localeCompare(a.location) : a.location.localeCompare(b.location)
      if (sortBy === 'applicants') {
        const aVal = parseInt(String(a.applicants).replace(/\D/g, '')) || 999; const bVal = parseInt(String(b.applicants).replace(/\D/g, '')) || 999
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      if (sortBy === 'created_at' || sortBy === 'posted_at') {
        const field = sortBy; const aVal = a[field] ? new Date(a[field]).getTime() : 0; const bVal = b[field] ? new Date(b[field]).getTime() : 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      return 0
    })
    return r
  }, [jobsWithLocations, sortBy, sortDir])

  const activeFilterCount = filterCities.length + filterCompanies.length + filterMatches.length + filterWorkTypes.length + filterEmploymentTypes.length + (filterTech ? 1 : 0)

  const openDrawer = (num) => {
    if (!jobs) return
    const j = jobs.find(x => x.num === num); const s = summaries?.find(x => x.num === num)
    // Find the tailored resume and cover letter for this job
    const r = resumes?.find(x => x.job_num === num && !x.id.startsWith('cover_')) ||
              resumes?.find(x => !x.id.startsWith('original') && !x.id.startsWith('cover_') && j.company.toLowerCase().includes((x.company || '').split(' ')[0].toLowerCase().replace(/[()]/g, '')))
    const cl = resumes?.find(x => x.job_num === num && x.id.startsWith('cover_'))
    setDrawer({ job: j, summary: s, resume: r, coverLetter: cl }); setDrawerTab('details')
  }

  const [generatingResume, setGeneratingResume] = useState(false)
  const [generatingCover, setGeneratingCover] = useState(false)

  const generateResume = async (num) => {
    setGeneratingResume(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { setToast(data.error || 'Failed'); return }
      // Update drawer with new resume
      setDrawer(prev => ({ ...prev, resume: { id: data.id, content: data.content, job_num: num } }))
      // Refresh resumes list
      fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))
      setToast('Resume generated!')
    } catch (e) { setToast('Generation failed') }
    finally { setGeneratingResume(false) }
  }

  const generateCover = async (num) => {
    setGeneratingCover(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { setToast(data.error || 'Failed'); return }
      setDrawer(prev => ({ ...prev, coverLetter: { id: data.id, content: data.content, job_num: num } }))
      fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))
      setToast('Cover letter generated!')
    } catch (e) { setToast('Generation failed') }
    finally { setGeneratingCover(false) }
  }

  const clearFilters = () => { setFilterCities([]); setFilterCompanies([]); setFilterTech(''); setFilterMatches([]); setFilterWorkTypes([]); setFilterEmploymentTypes([]) }

  const filterChangeRef = useRef(false)
  useEffect(() => {
    if (!filterChangeRef.current) { filterChangeRef.current = true; return }
    setJobsPage(0)
    const params = new URLSearchParams()
    params.set('offset', '0'); params.set('limit', String(JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => { setJobs(d.jobs || []); setJobsTotal(d.total || 0); setJobAgg(d.agg || {}) })
  }, [sortBy, sortDir, filterCities, filterCompanies, filterTech, filterMatches, filterWorkTypes, filterEmploymentTypes])

  const switchTab = (t) => { setTab(t); window.location.hash = t }

  const tabs = [
    { id: 'jobs', icon: <Briefcase className="w-4 h-4" />, label: 'Jobs', badge: jobsTotal, section: 'jobs' },
    { id: 'resume', icon: <FileText className="w-4 h-4" />, label: 'Resume', section: 'jobs' },
    { id: 'dashboard', icon: <ChartBar className="w-4 h-4" />, label: 'Dashboard', section: 'analysis' },
    { id: 'rules', icon: <Gear className="w-4 h-4" />, label: 'Rules', section: 'settings' },
  ]

  const refreshAnalysis = async () => { setRefreshing(r => ({ ...r, analysis: true })); try { await fetch(`${API}/refresh/analysis`, { method: 'POST' }); } catch {} refreshJobs(); await fetchAnalysis(); setRefreshing(r => ({ ...r, analysis: false })) }

  if (jobs === null) return <div className="flex items-center justify-center h-screen text-muted-foreground">Loading...</div>

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Mobile sidebar toggle */}
      <Button variant="outline" size="icon" className="fixed top-3 left-3 z-[60] lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X className="w-4 h-4" /> : <ListChecks className="w-4 h-4" />}
      </Button>
      {sidebarOpen && <div className="fixed inset-0 bg-black/40 z-[49] lg:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* Sidebar */}
      <aside className={cn(
        "fixed lg:relative inset-y-0 left-0 z-[50] lg:z-auto border-r flex flex-col transition-all duration-200 bg-card",
        sidebarOpen ? "w-[170px]" : "w-0 overflow-hidden"
      )}>
        <div className="pt-12 lg:pt-0 flex-1 overflow-y-auto">
          {['jobs', 'analysis', 'settings'].map(section => (
            <div key={section}>
              <div className="px-3 py-2 text-xs uppercase tracking-wider text-muted-foreground">{section}</div>
              {tabs.filter(t => t.section === section).map(t => (
                <button key={t.id} onClick={() => switchTab(t.id)}
                  className={cn("flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition w-full text-left",
                    tab === t.id ? "border-l-primary font-semibold text-primary" : "border-l-transparent text-muted-foreground")}>
                  <span>{t.icon}</span><span>{t.label}</span>
                  {t.badge && <Badge variant="default" className="ml-auto text-[0.55rem] h-5">{t.badge}</Badge>}
                </button>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-12 border-b flex items-center px-4 gap-4 lg:gap-6 shrink-0 fixed top-0 left-0 lg:left-[170px] right-0 z-40 bg-card">
          <span className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent ml-10 lg:ml-0 whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity" onClick={() => switchTab('jobs')}>Job Search</span>
          <div className="hidden sm:flex gap-3 text-[0.65rem] text-muted-foreground">
            <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" /><b className="text-foreground">{jobAgg.total || jobsTotal}</b> total</span>
            <span className="text-border">|</span>
            <span className="flex items-center gap-1"><Target className="w-3 h-3 text-green-500" /><b className="text-green-500">{jobAgg.high_match}</b> high match</span>
            <span className="text-border">|</span>
            <span className="flex items-center gap-1"><Rocket className="w-3 h-3 text-yellow-500" /><b className="text-yellow-500">{jobAgg.apply_now}</b> apply now</span>
            <span className="text-border">|</span>
            <span className="flex items-center gap-1"><House className="w-3 h-3 text-cyan-500" /><b className="text-cyan-500">{jobAgg.remote}</b> remote</span>
            <span className="text-border">|</span>
            <span className="flex items-center gap-1"><FileText className="w-3 h-3 text-primary" /><b className="text-primary">{resumes.filter(r => r.id?.startsWith('original')).length}</b> resume</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">

            {/* === JOBS TAB === */}
            {tab === 'jobs' && (() => {
              const pendingCount = pending.filter(p => p.status === 'pending').length
              const queuedCount = pending.filter(p => p.status === 'queued').length
              const processingCount = pending.filter(p => p.status === 'processing').length
              const failedCount = pending.filter(p => p.status === 'failed').length
              const stackedTotal = pendingCount + queuedCount + processingCount + failedCount

              const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
              const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
              const handleDragLeave = () => { setDragOverCol(null) }
              const handleDrop = (e, colId) => {
                e.preventDefault(); setDragOverCol(null)
                if (!dragId) return
                if (colId === 'pending') resetPending(dragId)
                else if (colId === 'queued') processPending(dragId)
                else if (colId === 'processing') processPending(dragId)
                setDragId(null)
              }

              return (
                <div className="flex gap-2 h-[calc(100vh-80px)]">
                  {/* Processing Jobs column */}
                  <div className="w-1/4 flex flex-col rounded-lg border overflow-hidden bg-card">
                    <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-primary/20">
                      <Gear className="w-4 h-4 text-primary" />
                      <span className="font-bold text-xs text-primary">Processing Jobs</span>
                      <Badge variant="default" className="ml-auto text-[0.5rem] h-4">{stackedTotal}</Badge>
                    </div>
                    <div className="flex flex-col flex-1 min-h-0 p-2">
                      {/* Add URL */}
                      <div className="rounded border p-1.5 shrink-0 mb-1 bg-muted min-w-0">
                        <Input type="url" value={urlInput} onChange={e => { setUrlInput(e.target.value); setUrlError('') }}
                          onKeyDown={e => e.key === 'Enter' && submitUrl()}
                          placeholder="Paste LinkedIn URL..."
                          className={cn("w-full h-7 rounded border text-[0.6rem] min-w-0", urlError && "border-destructive")} />
                        {urlError && <div className="text-[0.5rem] mt-1 px-0.5 flex items-center gap-1 text-destructive"><Warning className="w-2.5 h-2.5" /> {urlError}</div>}
                        <div className="flex items-center gap-1 mt-1">
                          <Button onClick={submitUrl} disabled={submitting || !urlInput.trim()} size="sm" className="flex-1 h-6 text-[0.55rem]">
                            {submitting ? '...' : processImmediately ? 'Add & Process' : 'Add'}
                          </Button>
                          <button
                            onClick={() => setProcessImmediately(v => !v)}
                            className={cn(
                              "shrink-0 h-6 px-1.5 rounded text-[0.5rem] font-medium border transition-colors",
                              processImmediately
                                ? "bg-primary text-primary-foreground border-primary"
                                : "bg-background text-muted-foreground border-border hover:bg-muted"
                            )}
                          >
                            {processImmediately ? 'Auto' : 'Queue'}
                          </button>
                        </div>
                      </div>
                      {/* Stacked sections */}
                      <div className="flex flex-col flex-1 min-h-0 gap-1">
                        {[
                          { id: 'pending', count: pendingCount, label: 'Pending', icon: <Clock className="w-3 h-3" />, color: 'gray', iconClass: 'text-gray-500', bgClass: 'bg-gradient-to-r from-gray-500/10 to-gray-500/5', borderClass: 'border-b border-gray-500/20', textClass: 'text-gray-600 dark:text-gray-400' },
                          { id: 'queued', count: queuedCount, label: 'Queued', icon: <Stack className="w-3 h-3" />, color: 'yellow', iconClass: 'text-yellow-500', bgClass: 'bg-gradient-to-r from-yellow-500/10 to-yellow-500/5', borderClass: 'border-b border-yellow-500/20', textClass: 'text-yellow-600 dark:text-yellow-500' },
                          { id: 'processing', count: processingCount, label: 'Processing', icon: <Gear className="w-3 h-3" />, color: 'blue', iconClass: 'text-blue-500', bgClass: 'bg-gradient-to-r from-blue-500/10 to-blue-500/5', borderClass: 'border-b border-blue-500/20', textClass: 'text-blue-600 dark:text-blue-500' },
                          { id: 'failed', count: failedCount, label: 'Failed', icon: <X className="w-3 h-3" />, color: 'red', iconClass: 'text-red-500', bgClass: 'bg-gradient-to-r from-red-500/10 to-red-500/5', borderClass: 'border-b border-red-500/20', textClass: 'text-red-600 dark:text-red-500' },
                        ].filter(s => s.count > 0).map(s => {
                          const isOpen = !collapsedSections[s.id]
                          return (
                            <div key={s.id} className={cn("flex flex-col rounded-lg border min-w-0 max-w-full overflow-hidden", isOpen ? "flex-1 min-h-0" : "")}>
                              <div onClick={() => setCollapsedSections(prev => ({ ...prev, [s.id]: !prev[s.id] }))}
                                className={cn("px-2 py-1 flex items-center gap-1 shrink-0 cursor-pointer select-none hover:bg-muted/50 transition", s.bgClass, s.borderClass)}>
                                <span className={s.iconClass}>{s.icon}</span>
                                <span className={cn("font-bold text-[0.6rem] uppercase tracking-wider", s.textClass)}>{s.label}</span>
                                <Badge variant="secondary" className="text-[0.5rem] h-4 ml-auto">{s.count}</Badge>
                                <span className="text-[0.5rem] text-muted-foreground">{isOpen ? '▾' : '▸'}</span>
                              </div>
                              {isOpen && s.id === 'pending' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'pending')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'pending')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'pending').map(p =>
                                      <ProcessingItem key={p.id} item={p} onProcess={() => processPending(p.id)} onDelete={() => deletePending(p.id)} onDragStart={e => handleDragStart(e, p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'queued' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'queued')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'queued')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'queued').map(p =>
                                      <ProcessingItem key={p.id} item={p} onProcess={() => processPending(p.id)} onDelete={() => deletePending(p.id)} onReset={() => resetPending(p.id)} onDragStart={e => handleDragStart(e, p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'processing' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'processing')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'processing')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'processing').map(p =>
                                      <ProcessingItem key={p.id} item={p} onDragStart={e => handleDragStart(e, p.id)}
                                        onPause={() => pausePending(p.id)} onDelete={() => deletePending(p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'failed' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0">
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'failed').map(p =>
                                      <ProcessingItem key={p.id} item={p} onDelete={() => deletePending(p.id)} onProcess={() => processPending(p.id)} onReset={() => resetPending(p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      {stackedTotal === 0 && <div className="text-center py-8 text-[0.6rem] text-muted-foreground shrink-0">All jobs processed</div>}
                    </div>
                  </div>

                  {/* Processed Jobs column */}
                  <div className="w-3/4 flex flex-col rounded-lg border overflow-hidden bg-card">
                    <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-green-500/10 to-green-500/5 border-b border-green-500/20">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="font-bold text-xs text-green-500">Processed Jobs</span>
                      <Badge variant="secondary" className="text-[0.5rem] h-4 bg-green-500/15 text-green-500">{filteredJobs.length}/{jobsTotal}</Badge>
                      <div className="flex items-center gap-0.5 ml-auto">
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => refreshJobs()} title="Refresh"><ArrowsClockwise className="w-3 h-3 text-green-500" /></Button>
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => rescoreAll()} title="Rescore all"><TrendUp className="w-3 h-3 text-primary" /></Button>
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => reprocessAll()} title="Reprocess all"><Repeat className="w-3 h-3 text-yellow-500" /></Button>
                      </div>
                    </div>
                    <div ref={jobsScrollRef} className="flex-1 overflow-y-auto">
                      <div className="sticky top-0 z-10 bg-card p-2 pb-0">
                        <div className="flex items-center gap-1 mb-2">
                          <div className="relative flex-1">
                            <Input value={filterTech} onChange={e => setFilterTech(e.target.value)}
                              placeholder="Search by role, company, stack, or notes..."
                              className={cn("w-full h-7 text-xs", filterTech && "border-primary")} />
                            {filterTech && <button onClick={() => setFilterTech('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-[0.55rem] text-muted-foreground">✕</button>}
                          </div>
                          {activeFilterCount > 0 && <Button variant="ghost" size="sm" className="h-7 text-[0.6rem] text-destructive hover:text-destructive" onClick={clearFilters}>Clear all</Button>}
                        </div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-1">
                            <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setSortDir('desc') }}>
                              <SelectTrigger className="h-7 w-auto text-[0.6rem]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="created_at">Newest first</SelectItem>
                                <SelectItem value="posted_at">Posted date</SelectItem>
                                <SelectItem value="score">Score (Fit)</SelectItem>
                                <SelectItem value="score_success">Score (Success)</SelectItem>
                                <SelectItem value="score_combined">Score (Combined)</SelectItem>
                                <SelectItem value="applicants">Applicants</SelectItem>
                                <SelectItem value="company">Company</SelectItem>
                                <SelectItem value="location">Location</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button variant="outline" size="sm" className="h-7 text-[0.6rem]" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                              {sortDir === 'desc' ? '↓' : '↑'}
                            </Button>
                          </div>
                          <div className="flex items-center gap-1 flex-wrap justify-end">
                            <MultiSelect value={filterCities} onChange={setFilterCities} placeholder="City" icon={<MapPin className="w-3 h-3" />} options={allCities.map(c => ({ value: c, label: c }))} />
                            <MultiSelect value={filterCompanies} onChange={setFilterCompanies} placeholder="Co" icon={<Buildings className="w-3 h-3" />} options={allCompanies.map(c => ({ value: c, label: c }))} />
                            <MultiSelect value={filterMatches} onChange={setFilterMatches} placeholder="Match" icon={<Target className="w-3 h-3" />} options={[{ value: 'High', label: 'High' }, { value: 'Medium', label: 'Medium' }, { value: 'Low', label: 'Low' }]} />
                            <MultiSelect value={filterWorkTypes} onChange={setFilterWorkTypes} placeholder="Work" icon={<HouseSimple className="w-3 h-3" />} options={[{ value: 'On-site', label: 'On-site' }, { value: 'Remote', label: 'Remote' }, { value: 'Hybrid', label: 'Hybrid' }]} />
                            <MultiSelect value={filterEmploymentTypes} onChange={setFilterEmploymentTypes} placeholder="Emp" icon={<Briefcase className="w-3 h-3" />} options={[{ value: 'Full-time', label: 'Full-time' }, { value: 'Part-time', label: 'Part-time' }, { value: 'Contract', label: 'Contract' }, { value: 'Internship', label: 'Internship' }, { value: 'Temporary', label: 'Temporary' }]} alignRight />
                          </div>
                        </div>
                      </div>
                      <div className="p-2">
                        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                          {filteredJobs.map((j, i) => <JobCard key={j.num} job={j} rank={i + 1} onClick={() => openDrawer(j.num)} onRescore={rescoreJob} onDelete={deleteJob} onRequeue={requeueJob} onViewWorkflow={openWorkflow} />)}
                        </div>
                        <div ref={jobsSentinelRef} className="h-1" />
                        {loadingMore && <div className="text-center py-2 text-[0.6rem] text-muted-foreground">Loading more...</div>}
                        {!loadingMore && filteredJobs.length >= jobsTotal && filteredJobs.length > 0 && <div className="text-center py-2 text-[0.55rem] text-muted-foreground opacity-50">All {jobsTotal} jobs loaded</div>}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}

            {/* === DASHBOARD TAB === */}
            {tab === 'dashboard' && (() => {
              const analysisData = analysis?.analysis || {}
              const hasAnalysis = !!analysis?.analysis
              const overview = analysisData.overview || {}
              const strategy = analysisData.strategy || []
              const strengths = analysisData.strengths || []
              const weaknesses = analysisData.weaknesses || []
              const visaCompanies = analysisData.visa_companies || []
              const applyUrgency = analysisData.apply_urgency || []
              const techStackData = analysisData.techStack || []
              const techLearningData = analysisData.techLearning || []
              const skillJobFit = analysisData.skillJobFit || []
              const learningROI = analysisData.learningROI || []
              const searchSummary = analysisData.searchSummary || {}
              const improvements = analysisData.improvements || []
              const goals = analysisData.goals || []
              const networking = analysisData.networking || []

              const highMatchJobs = jobs.filter(j => j.match === 'High')
              const applyNow = jobs.filter(j => ['A', 'A+', 'A++'].includes(j.score))
              const remoteJobs = jobs.filter(j => j.work_type === 'Remote')
              const visaReady = jobs.filter(j => j.visa === 'BEST' || j.visa === 'Strong')

              const strongStack = techStackData.filter(t => t.mc === 'p1') || []
              const midStack = techStackData.filter(t => t.mc === 'p2') || []
              const weakStack = techStackData.filter(t => t.mc === 'p3' || t.mc === 'p4') || []
              const p1Tech = techLearningData.filter(t => t.pc === 'p1') || []
              const p2Tech = techLearningData.filter(t => t.pc === 'p2') || []
              const totalUsage = techStackData.reduce((sum, t) => sum + (t.level || 0), 0) || 0
              const avgLevel = techStackData.length ? (totalUsage / techStackData.length).toFixed(1) : 0

              return (
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <h2 className="text-xl font-extrabold">Dashboard</h2>
                      <Tabs value={dashboardSubTab} onValueChange={setDashboardSubTab}>
                        <TabsList className="bg-muted">
                          <TabsTrigger value="overview"><ChartBar className="w-4 h-4 mr-1.5" />Overview</TabsTrigger>
                          <TabsTrigger value="strategy"><Target className="w-4 h-4 mr-1.5" />Strategy</TabsTrigger>
                          <TabsTrigger value="networking"><Users className="w-4 h-4 mr-1.5" />Networking</TabsTrigger>
                          <TabsTrigger value="skills"><Brain className="w-4 h-4 mr-1.5" />Skills</TabsTrigger>
                        </TabsList>
                      </Tabs>
                      <p className="text-xs text-muted-foreground">
                        {analysis?.created_at && <span>Last updated: {new Date(analysis.created_at).toLocaleString()}</span>}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button onClick={refreshAnalysis} disabled={refreshing.analysis} variant={refreshing.analysis ? "secondary" : "outline"} size="sm" className="gap-1.5">
                        <ArrowsClockwise className={cn("w-3.5 h-3.5", refreshing.analysis && "animate-spin")} />
                        {refreshing.analysis ? 'Updating...' : 'Refresh All'}
                      </Button>
                    </div>
                  </div>

                  {!hasAnalysis && !refreshing.analysis && (
                    <Card className="p-8 text-center border-dashed">
                      <ChartBar className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
                      <p className="text-sm font-semibold mb-1">No analysis data yet</p>
                      <p className="text-xs text-muted-foreground mb-4">Click "Refresh Analysis" to generate insights from your {jobs.length} processed jobs.</p>
                      <Button onClick={refreshAnalysis} size="sm" className="gap-1.5">
                        <ArrowsClockwise className="w-3.5 h-3.5" /> Generate Analysis
                      </Button>
                    </Card>
                  )}

                  {/* OVERVIEW */}
                  {dashboardSubTab === 'overview' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <h3 className="font-extrabold text-sm">Overview</h3>
                        <Button variant="ghost" size="sm" onClick={refreshAnalysis} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
                          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
                        </Button>
                      </div>
                      <div className="grid grid-cols-6 gap-3">
                        {[
                          { n: overview.totalJobs || jobs.length, l: 'Total Jobs', c: 'text-primary', icon: <Briefcase className="w-5 h-5" /> },
                          { n: overview.highMatch || highMatchJobs.length, l: 'High Match', c: 'text-green-500', icon: <Target className="w-5 h-5" /> },
                          { n: overview.applyNow || applyNow.length, l: 'Apply Now (75+)', c: 'text-yellow-500', icon: <Rocket className="w-5 h-5" /> },
                          { n: overview.remoteJobs || remoteJobs.length, l: 'Remote', c: 'text-cyan-500', icon: <House className="w-5 h-5" /> },
                          { n: overview.visaReady || visaReady.length, l: 'Visa Ready', c: 'text-purple-500', icon: <IdentificationCard className="w-5 h-5" /> },
                          { n: resumes.filter(r => r.id !== 'original').length, l: 'Resumes', c: 'text-primary', icon: <FileText className="w-5 h-5" /> },
                        ].map((s, i) => (
                          <Card key={i} className="p-4 transition hover:border-primary">
                            <div className={cn("mb-1", s.c)}>{s.icon}</div>
                            <div className={cn("text-2xl font-extrabold", s.c)}>{s.n}</div>
                            <div className="text-[0.65rem] uppercase tracking-wider mt-0.5 text-muted-foreground">{s.l}</div>
                          </Card>
                        ))}
                      </div>

                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Rocket className="w-5 h-5 text-yellow-500" />
                              <h3 className="font-extrabold text-sm">Apply Now — Score 75+</h3>
                              <Badge variant="secondary" className="text-[0.6rem] bg-green-500/15 text-green-500">{applyNow.length} jobs</Badge>
                            </div>
                            {applyNow.length === 0 ? <div className="text-center py-6 text-xs text-muted-foreground">No jobs scored A or above yet</div> : (
                              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                                {applyNow.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                              </div>
                            )}
                          </Card>

                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Target className="w-5 h-5 text-green-500" />
                              <h3 className="font-extrabold text-sm">High Match Jobs</h3>
                              <Badge variant="secondary" className="text-[0.6rem] bg-green-500/15 text-green-500">{highMatchJobs.length} jobs</Badge>
                            </div>
                            {highMatchJobs.length === 0 ? <div className="text-center py-6 text-xs text-muted-foreground">No high match jobs</div> : (
                              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                                {highMatchJobs.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                              </div>
                            )}
                          </Card>

                          {skillJobFit.length > 0 && (
                            <Card className="p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <Link className="w-5 h-5 text-primary" />
                                <h3 className="font-extrabold text-sm">Skill-Job Fit Analysis</h3>
                              </div>
                              <div className="space-y-2">
                                {skillJobFit.slice(0, 8).map((item, i) => (
                                  <div key={i} className="flex items-center gap-3 text-xs p-2 rounded-lg hover:bg-muted transition">
                                    <div className="w-24 font-semibold">{item.skill}</div>
                                    <Progress value={item.fitScore} className="flex-1 h-2" />
                                    <div className="w-12 text-right font-bold text-primary">{item.fitScore}%</div>
                                    <div className="w-20 text-right text-muted-foreground">{item.jobsRequiring}/{overview.totalJobs || jobs.length}</div>
                                  </div>
                                ))}
                              </div>
                            </Card>
                          )}
                        </div>

                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Globe className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Cities</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              {cities?.slice(0, 6).map((c, i) => (
                                <Card key={i} className="p-2 text-center transition hover:border-primary">
                                  <div className="mb-0.5 text-primary"><EmojiIcon emoji={c.icon} /></div>
                                  <div className="font-bold text-xs">{c.name}</div>
                                  <div className="text-[0.55rem] text-muted-foreground">{c.info}</div>
                                  <div className="text-[0.55rem] font-semibold text-primary">{c.jobs}</div>
                                </Card>
                              ))}
                            </div>
                          </Card>

                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <IdentificationCard className="w-5 h-5 text-purple-500" />
                              <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
                            </div>
                            {visaCompanies.length > 0 ? (
                              <div className="space-y-1.5">
                                {visaCompanies.slice(0, 6).map((j, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-muted transition">
                                    <span className="font-semibold">{j.company}</span>
                                    <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{j.visa}</Badge>
                                  </div>
                                ))}
                              </div>
                            ) : <div className="text-xs text-muted-foreground">No visa data yet</div>}
                          </Card>

                          {/* Profile Status */}
                          {(() => {
                            const latestResume = resumes.filter(r => r.id?.startsWith('original_')).sort((a, b) => (b.version || 0) - (a.version || 0))[0]
                            const latestLinkedin = linkedinProfiles.filter(p => p.id?.startsWith('linkedin_')).sort((a, b) => (b.version || 0) - (a.version || 0))[0]
                            if (!latestResume && !latestLinkedin) return null
                            return (
                              <Card className="p-4">
                                <div className="flex items-center gap-2 mb-3">
                                  <FileText className="w-5 h-5 text-primary" />
                                  <h3 className="font-extrabold text-sm">Your Profile</h3>
                                </div>
                                <div className="space-y-2">
                                  {latestResume && (
                                    <div className="flex items-center justify-between text-xs">
                                      <span className="flex items-center gap-1.5"><FileText className="w-3 h-3 text-green-500" /> Resume</span>
                                      <Badge variant="secondary" className="text-[0.5rem]">v{latestResume.version}</Badge>
                                    </div>
                                  )}
                                  {latestLinkedin && (
                                    <div className="flex items-center justify-between text-xs">
                                      <span className="flex items-center gap-1.5"><LinkedinLogo className="w-3 h-3 text-[#0A66C2]" /> LinkedIn</span>
                                      <Badge variant="secondary" className="text-[0.5rem]">v{latestLinkedin.version}</Badge>
                                    </div>
                                  )}
                                  {!latestResume && (
                                    <div className="text-[0.6rem] text-yellow-500">No resume uploaded</div>
                                  )}
                                </div>
                              </Card>
                            )
                          })()}

                          {/* Scoring Rules Summary */}
                          {rules && rules.length > 0 && (() => {
                            const fitRules = rules.filter(r => r.category === 'fit' && r.enabled)
                            const successRules = rules.filter(r => r.category === 'success' && r.enabled)
                            if (fitRules.length === 0 && successRules.length === 0) return null
                            return (
                              <Card className="p-4">
                                <div className="flex items-center gap-2 mb-3">
                                  <Gear className="w-5 h-5 text-primary" />
                                  <h3 className="font-extrabold text-sm">Scoring Rules</h3>
                                  <Badge variant="secondary" className="text-[0.5rem]">{fitRules.length + successRules.length} active</Badge>
                                </div>
                                <div className="space-y-2">
                                  <div>
                                    <div className="text-[0.6rem] text-muted-foreground mb-1">Fit Rules ({fitRules.length})</div>
                                    <div className="space-y-0.5">
                                      {fitRules.slice(0, 4).map((r, i) => (
                                        <div key={i} className="text-[0.6rem] text-muted-foreground truncate" title={r.value}>
                                          <span className="font-semibold text-foreground/70">#{r.priority}</span> {r.key}
                                        </div>
                                      ))}
                                      {fitRules.length > 4 && <div className="text-[0.55rem] text-muted-foreground/60">+{fitRules.length - 4} more</div>}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-[0.6rem] text-muted-foreground mb-1">Success Rules ({successRules.length})</div>
                                    <div className="space-y-0.5">
                                      {successRules.slice(0, 4).map((r, i) => (
                                        <div key={i} className="text-[0.6rem] text-muted-foreground truncate" title={r.value}>
                                          <span className="font-semibold text-foreground/70">#{r.priority}</span> {r.key}
                                        </div>
                                      ))}
                                      {successRules.length > 4 && <div className="text-[0.55rem] text-muted-foreground/60">+{successRules.length - 4} more</div>}
                                    </div>
                                  </div>
                                </div>
                              </Card>
                            )
                          })()}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* STRATEGY */}
                  {dashboardSubTab === 'strategy' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <h3 className="font-extrabold text-sm">Strategy</h3>
                        <Button variant="ghost" size="sm" onClick={refreshAnalysis} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
                          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
                        </Button>
                      </div>
                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          {/* Action Items — merged Strategy Guide + Must Improve */}
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Clipboard className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Action Items</h3>
                              {strategy.length === 0 && improvements.length === 0 && <Badge variant="secondary" className="text-[0.55rem]">Processing...</Badge>}
                            </div>
                            <div className="space-y-2">
                              {strategy.map((g, i) => (
                                <div key={`s-${i}`} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-muted border-l-2 border-primary">
                                  <span className="shrink-0 text-primary"><EmojiIcon emoji={g.icon} /></span>
                                  <div>
                                    <div className="font-bold text-xs">{g.title}</div>
                                    <div className="text-[0.6rem] text-muted-foreground">{g.description}</div>
                                  </div>
                                </div>
                              ))}
                              {improvements.map((item, i) => (
                                <div key={`i-${i}`} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-muted border-l-2 border-orange-500">
                                  <Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5 text-orange-500" />
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-xs">{item.area}</span>
                                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5", item.priority === 'high' ? "bg-red-500/15 text-red-500" : item.priority === 'medium' ? "bg-yellow-500/15 text-yellow-500" : "bg-blue-500/15 text-blue-500")}>
                                        {item.priority}
                                      </Badge>
                                    </div>
                                    <div className="text-[0.6rem] text-muted-foreground">{item.action}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </Card>

                          {applyUrgency.length > 0 && (
                            <Card className="p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <Lightning className="w-5 h-5 text-yellow-500" />
                                <h3 className="font-extrabold text-sm">Urgent Applications</h3>
                              </div>
                              <div className="space-y-1.5">
                                {applyUrgency.map((item, i) => (
                                  <div key={i} className="flex items-start gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                                    <span className="font-semibold">{item.company}</span>
                                    <span className="text-muted-foreground">- {item.reason}</span>
                                  </div>
                                ))}
                              </div>
                            </Card>
                          )}

                          {goals.length > 0 && (
                            <Card className="p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <Target className="w-5 h-5 text-cyan-500" />
                                <h3 className="font-extrabold text-sm">Goals & Best Practices</h3>
                              </div>
                              <div className="space-y-2">
                                {goals.map((g, i) => (
                                  <div key={i} className="flex items-start gap-2 p-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                                    <Target className="w-3.5 h-3.5 shrink-0 mt-0.5 text-cyan-500" />
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2 mb-0.5">
                                        <span className="font-bold text-xs text-cyan-500">{g.title}</span>
                                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">{g.timeline}</Badge>
                                      </div>
                                      <div className="text-[0.6rem] text-muted-foreground">{g.bestPractice}</div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </Card>
                          )}
                        </div>

                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <TrendUp className="w-5 h-5 text-green-500" />
                              <h3 className="font-extrabold text-sm">Your Strengths</h3>
                            </div>
                            {strengths.length > 0 ? (
                              <div className="space-y-1.5">
                                {strengths.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                    <span className="font-semibold">{t.name}</span>
                                    <span className="text-muted-foreground">- {t.detail}</span>
                                  </div>
                                ))}
                              </div>
                            ) : <div className="text-xs text-muted-foreground">No strong matches yet</div>}
                          </Card>

                          {searchSummary.totalSearched > 0 && (
                            <Card className="p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <MagnifyingGlass className="w-5 h-5 text-primary" />
                                <h3 className="font-extrabold text-sm">Search Summary</h3>
                              </div>
                              <div className="space-y-1.5 text-xs">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Jobs Analyzed</span>
                                  <span className="font-bold">{searchSummary.totalSearched}</span>
                                </div>
                                {searchSummary.avgApplicants > 0 && (
                                  <div className="flex justify-between">
                                    <span className="text-muted-foreground">Avg Applicants</span>
                                    <span className="font-bold">{Math.round(searchSummary.avgApplicants)}</span>
                                  </div>
                                )}
                                {searchSummary.dateRange && (
                                  <div className="flex justify-between">
                                    <span className="text-muted-foreground">Date Range</span>
                                    <span className="font-bold text-[0.6rem]">{searchSummary.dateRange}</span>
                                  </div>
                                )}
                                {searchSummary.topCompanies?.length > 0 && (
                                  <div className="mt-1.5">
                                    <div className="text-[0.6rem] text-muted-foreground mb-1">Top Companies</div>
                                    <div className="flex flex-wrap gap-1">
                                      {searchSummary.topCompanies.slice(0, 5).map((c, i) => (
                                        <Badge key={i} variant="secondary" className="text-[0.5rem]">{c}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {searchSummary.topRoles?.length > 0 && (
                                  <div className="mt-1.5">
                                    <div className="text-[0.6rem] text-muted-foreground mb-1">Top Roles</div>
                                    <div className="flex flex-wrap gap-1">
                                      {searchSummary.topRoles.slice(0, 5).map((r, i) => (
                                        <Badge key={i} variant="secondary" className="text-[0.5rem]">{r}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {searchSummary.pattern && (
                                  <div className="mt-2 p-2 rounded bg-muted text-[0.6rem] text-muted-foreground">
                                    {searchSummary.pattern}
                                  </div>
                                )}
                              </div>
                            </Card>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* NETWORKING */}
                  {dashboardSubTab === 'networking' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <h3 className="font-extrabold text-sm">Networking</h3>
                        <Button variant="ghost" size="sm" onClick={refreshAnalysis} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
                          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
                        </Button>
                      </div>
                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Users className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Networking Targets</h3>
                              {networking.length === 0 && <Badge variant="secondary" className="text-[0.55rem]">Processing...</Badge>}
                            </div>
                            <p className="text-[0.6rem] text-muted-foreground mb-3">Top companies to connect with on LinkedIn. Reach out to recruiters and engineering staff to increase your visibility.</p>
                            <div className="space-y-3">
                              {networking.map((item, i) => (
                                <div key={i} className="rounded-lg border p-3 space-y-2.5 hover:shadow transition">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <span className="font-extrabold text-sm">{item.company}</span>
                                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                                        item.score === 'A++' || item.score === 'A+' ? "bg-green-500/15 text-green-500" :
                                        item.score === 'A' ? "bg-blue-500/15 text-blue-500" :
                                        "bg-yellow-500/15 text-yellow-500"
                                      )}>{item.score}</Badge>
                                      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                                        item.match === 'High' ? "bg-green-500/15 text-green-500" :
                                        item.match === 'Medium' ? "bg-yellow-500/15 text-yellow-500" :
                                        "bg-gray-500/15 text-gray-500"
                                      )}>{item.match}</Badge>
                                    </div>
                                    {item.jobUrl && (
                                      <a href={item.jobUrl} target="_blank" rel="noopener noreferrer"
                                        className="text-[0.55rem] text-primary hover:underline flex items-center gap-1">
                                        <Link className="w-3 h-3" /> View Job
                                      </a>
                                    )}
                                    {item.company_url && (
                                      <a href={item.company_url} target="_blank" rel="noopener noreferrer"
                                        className="text-[0.55rem] text-muted-foreground hover:text-primary hover:underline flex items-center gap-1">
                                        <Globe className="w-3 h-3" /> Website
                                      </a>
                                    )}
                                  </div>
                                  {item.roles && item.roles.length > 0 && (
                                    <div className="flex flex-wrap gap-1">
                                      {item.roles.map((r, ri) => (
                                        <Badge key={ri} variant="outline" className="text-[0.45rem] h-3.5">{r}</Badge>
                                      ))}
                                    </div>
                                  )}
                                  <div className="text-[0.6rem] text-muted-foreground">{item.reason}</div>

                                  {/* Recruiter links */}
                                  {item.recruiters && item.recruiters.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="flex items-center gap-1.5">
                                        <IdentificationCard className="w-3 h-3 text-purple-500" />
                                        <span className="text-[0.55rem] font-bold text-purple-500">Recruiters & Talent</span>
                                      </div>
                                      {item.recruiters.map((r, ri) => (
                                        <a key={ri} href={r.linkedinSearch} target="_blank" rel="noopener noreferrer"
                                          className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                                          {r.title || r.name}
                                        </a>
                                      ))}
                                    </div>
                                  )}

                                  {/* Engineer links */}
                                  {item.engineers && item.engineers.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="flex items-center gap-1.5">
                                        <Gear className="w-3 h-3 text-blue-500" />
                                        <span className="text-[0.55rem] font-bold text-blue-500">Software Engineers</span>
                                      </div>
                                      {item.engineers.map((e, ei) => (
                                        <a key={ei} href={e.linkedinSearch} target="_blank" rel="noopener noreferrer"
                                          className="flex items-center gap-1.5 text-[0.55rem] text-primary hover:underline pl-4">
                                          <MagnifyingGlass className="w-2.5 h-2.5 shrink-0" />
                                          {e.title || e.name}
                                        </a>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                              {networking.length === 0 && !refreshing.analysis && (
                                <div className="text-xs text-muted-foreground text-center py-4">
                                  Run analysis to generate networking targets.
                                </div>
                              )}
                            </div>
                          </Card>
                        </div>

                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Lightbulb className="w-5 h-5 text-yellow-500" />
                              <h3 className="font-extrabold text-sm">Networking Tips</h3>
                            </div>
                            <div className="space-y-2 text-[0.6rem] text-muted-foreground">
                              <div className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                                <span>Search for <strong>Recruiters</strong> and <strong>Talent Acquisition</strong> at each company first — they control the hiring pipeline.</span>
                              </div>
                              <div className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                                <span>Connect with <strong>Software Engineers</strong> and <strong>Backend Engineers</strong> — they can refer you internally and share team culture.</span>
                              </div>
                              <div className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                                <span>Personalize your connection request — mention the specific role and why you're interested in their company.</span>
                              </div>
                              <div className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                                <span>Engage with their posts before connecting — like, comment, and share to build familiarity.</span>
                              </div>
                              <div className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-green-500" />
                                <span>Follow up 1 week after connecting with a brief message about your interest in the role.</span>
                              </div>
                            </div>
                          </Card>

                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <LinkedinLogo className="w-5 h-5 text-[#0A66C2]" />
                              <h3 className="font-extrabold text-sm">Quick Searches</h3>
                            </div>
                            <div className="space-y-1.5">
                              <a href="https://www.google.com/search?q=site:linkedin.com/in+%22recruiter%22+%22software+engineer%22+Berlin" target="_blank" rel="noopener noreferrer"
                                className="flex items-center gap-2 text-[0.6rem] text-primary hover:underline p-1.5 rounded hover:bg-muted transition">
                                <MagnifyingGlass className="w-3 h-3" />
                                Recruiters — Software Engineers Berlin
                              </a>
                              <a href="https://www.google.com/search?q=site:linkedin.com/in+%22talent+acquisition%22+%22backend%22+Berlin" target="_blank" rel="noopener noreferrer"
                                className="flex items-center gap-2 text-[0.6rem] text-primary hover:underline p-1.5 rounded hover:bg-muted transition">
                                <MagnifyingGlass className="w-3 h-3" />
                                Talent Acquisition — Backend Berlin
                              </a>
                              <a href="https://www.google.com/search?q=site:linkedin.com/in+%22hiring+manager%22+%22python%22+Berlin" target="_blank" rel="noopener noreferrer"
                                className="flex items-center gap-2 text-[0.6rem] text-primary hover:underline p-1.5 rounded hover:bg-muted transition">
                                <MagnifyingGlass className="w-3 h-3" />
                                Hiring Managers — Python Berlin
                              </a>
                            </div>
                          </Card>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SKILLS */}
                  {dashboardSubTab === 'skills' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <h3 className="font-extrabold text-sm">Skills</h3>
                        <Button variant="ghost" size="sm" onClick={refreshAnalysis} disabled={refreshing.analysis} className="gap-1 h-6 text-[0.55rem]">
                          <ArrowsClockwise className={cn("w-3 h-3", refreshing.analysis && "animate-spin")} /> Refresh
                        </Button>
                      </div>
                      <div className="grid grid-cols-5 gap-3">
                        {[
                          { n: techStackData.length || 0, l: 'Total Skills', c: 'text-primary', icon: <Wrench className="w-5 h-5" /> },
                          { n: strongStack.length, l: 'Strong Match', c: 'text-green-500', icon: <TrendUp className="w-5 h-5" /> },
                          { n: midStack.length, l: 'Moderate', c: 'text-blue-500', icon: <Stack className="w-5 h-5" /> },
                          { n: weakStack.length, l: 'Gaps', c: 'text-yellow-500', icon: <BookOpen className="w-5 h-5" /> },
                          { n: `${avgLevel}/5`, l: 'Avg Level', c: 'text-purple-500', icon: <ChartBar className="w-5 h-5" /> },
                        ].map((s, i) => (
                          <Card key={i} className="p-3 text-center transition hover:border-primary">
                            <div className="text-lg mb-0.5">{s.icon}</div>
                            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
                            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
                          </Card>
                        ))}
                      </div>

                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Gear className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Current Tech Stack</h3>
                              <Badge variant="secondary" className="text-[0.55rem]">{techStackData.length || 0} skills</Badge>
                            </div>
                            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                              {techStackData.map((t, i) => <StackCard key={i} tech={t} />)}
                            </div>
                          </Card>

                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Brain className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Technologies to Master</h3>
                              <Badge variant="secondary" className="text-[0.55rem] bg-green-500/15 text-green-500">{techLearningData.length || 0} items</Badge>
                            </div>
                            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                              {techLearningData.map((t, i) => <TechCard key={i} tech={t} />)}
                            </div>
                          </Card>
                        </div>

                        <div className="space-y-4">
                          {/* What to Learn — merged: weaknesses + learning priorities + skill gaps */}
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-5 h-5 text-yellow-500" />
                              <h3 className="font-extrabold text-sm">What to Learn</h3>
                            </div>
                            <div className="space-y-1.5">
                              {p1Tech.map((t, i) => (
                                <div key={`p1-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                  <span className="font-semibold">{t.name}</span>
                                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.reason}</span>
                                  <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500 shrink-0">P1</Badge>
                                </div>
                              ))}
                              {p2Tech.map((t, i) => (
                                <div key={`p2-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                  <span className="font-semibold">{t.name}</span>
                                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.reason}</span>
                                  <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-blue-500/15 text-blue-500 shrink-0">P2</Badge>
                                </div>
                              ))}
                              {weaknesses.filter(w => !p1Tech.some(p => p.name === w.name) && !p2Tech.some(p => p.name === w.name)).map((t, i) => (
                                <div key={`w-${i}`} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                                  <span className="font-semibold">{t.name}</span>
                                  <span className="text-muted-foreground text-[0.55rem] truncate flex-1">{t.detail}</span>
                                </div>
                              ))}
                              {p1Tech.length === 0 && p2Tech.length === 0 && weaknesses.length === 0 && (
                                <div className="text-xs text-muted-foreground">No major gaps</div>
                              )}
                            </div>
                          </Card>

                          {learningROI.length > 0 && (
                            <Card className="p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <ChartLineUp className="w-5 h-5 text-primary" />
                                <h3 className="font-extrabold text-sm">Learning ROI</h3>
                              </div>
                              <div className="space-y-1.5">
                                {learningROI.slice(0, 5).map((item, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted transition">
                                    <span className="font-semibold w-20 truncate">{item.skill}</span>
                                    <div className="flex-1 h-[3px] rounded-full bg-muted">
                                      <div className="h-full rounded-full bg-primary" style={{ width: `${item.impactScore * 10}%` }} />
                                    </div>
                                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5 shrink-0", item.impactScore >= 7 ? "bg-green-500/15 text-green-500" : "bg-yellow-500/15 text-yellow-500")}>
                                      {item.impactScore}/10
                                    </Badge>
                                    <span className="text-muted-foreground text-[0.55rem] shrink-0">{item.timeToLearn}</span>
                                  </div>
                                ))}
                              </div>
                            </Card>
                          )}

                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <ChartBar className="w-5 h-5 text-primary" />
                              <h3 className="font-extrabold text-sm">Level Distribution</h3>
                            </div>
                            <div className="space-y-2">
                              {[
                                { label: 'Strong (5/5)', count: strongStack.length, color: 'bg-green-500' },
                                { label: 'Good (4/5)', count: techStackData.filter(t => t.level === 4).length || 0, color: 'bg-blue-500' },
                                { label: 'Moderate (3/5)', count: techStackData.filter(t => t.level === 3).length || 0, color: 'bg-yellow-500' },
                                { label: 'Basic (2/5)', count: techStackData.filter(t => t.level === 2).length || 0, color: 'bg-orange-500' },
                                { label: 'Beginner (1/5)', count: techStackData.filter(t => t.level === 1).length || 0, color: 'bg-red-500' },
                              ].map((s, i) => (
                                <div key={i} className="flex items-center gap-2">
                                  <div className="w-20 text-[0.6rem] text-muted-foreground">{s.label}</div>
                                  <Progress value={techStackData.length ? (s.count / techStackData.length * 100) : 0} className="flex-1 h-2" />
                                  <div className={cn("w-6 text-right text-[0.6rem] font-bold", s.color.replace('bg-', 'text-'))}>{s.count}</div>
                                </div>
                              ))}
                            </div>
                          </Card>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}

            {/* === RESUME === */}
            {tab === 'resume' && <ResumeTab resumes={resumes} linkedinProfiles={linkedinProfiles} onRefreshResumes={() => fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))} onRefreshLinkedin={() => fetch(`${API}/linkedin`).then(r => r.json()).then(r => setLinkedinProfiles(r))} />}

            {/* === PREFERENCES === */}
            {tab === 'rules' && <RulesTab rules={rules} onUpdate={fetchRules} />}
          </div>
        </div>
      </main>

      {/* Job Details Drawer */}
      <Sheet open={!!drawer} onOpenChange={(open) => !open && setDrawer(null)}>
        <SheetContent className="w-[min(640px,92vw)] sm:max-w-[640px] overflow-y-auto p-4 pr-12">
          {drawer && (() => {
            const drawerLocations = (() => {
              if (drawer.job.locations) {
                try { const locs = typeof drawer.job.locations === 'string' ? JSON.parse(drawer.job.locations) : drawer.job.locations; return locs.length ? locs : [drawer.job.location] } catch { return [drawer.job.location] }
              }
              return [drawer.job.location]
            })()
            return (
              <>
                <SheetHeader className="mb-4">
                  <div className="flex gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className={cn("text-4xl font-black", getScoreColor(drawer.job.score))}>{drawer.job.score}</div>
                        {drawer.job.success && (
                          <div className={cn("text-lg font-bold opacity-80", getScoreColor(drawer.job.success))}>{drawer.job.success}</div>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => rescoreJob(drawer.job.num)} title="Rescore">
                          <TrendUp className="w-3.5 h-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => requeueJob(drawer.job.num)} title="Reprocess from scratch">
                          <Repeat className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                      <SheetTitle className="text-lg">{drawer.job.company}</SheetTitle>
                      <SheetDescription>{drawer.job.role}</SheetDescription>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {drawer.job.industry && <Badge variant="secondary" className="text-[0.55rem] bg-primary/10 text-primary">{drawer.job.industry}</Badge>}
                        {drawerLocations.map((loc, i) => <LocationBadge key={i} loc={loc} />)}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      <Badge variant="outline" className={cn("uppercase border", getMatchClass(drawer.job.match))}>{drawer.job.match}</Badge>
                      {drawer.job.action && (
                        <div className="text-[0.6rem] font-semibold px-2 py-1 rounded-lg text-right max-w-[180px]"
                          style={{ background: ['A','A+','A++'].includes(drawer.job.score) ? 'rgba(34,197,94,0.12)' : ['B','C'].includes(drawer.job.score) ? 'rgba(234,179,8,0.12)' : 'rgba(239,68,68,0.12)', color: ['A','A+','A++'].includes(drawer.job.score) ? '#22c55e' : ['B','C'].includes(drawer.job.score) ? '#eab308' : '#ef4444' }}>
                          {drawer.job.action}
                        </div>
                      )}
                      {drawer.job.visa && drawer.job.visa !== 'Uncertain' && <VisaBadge visa={drawer.job.visa} />}
                      {drawer.job.work_type && <Badge variant="secondary">{drawer.job.work_type}</Badge>}
                    </div>
                  </div>
                </SheetHeader>

                <div className="flex gap-2 mb-3">
                  <a href={drawer.job.url} target="_blank" rel="noreferrer" className="flex-1">
                    <Button className="w-full gap-2"><Link className="w-4 h-4" /> Open Job Page</Button>
                  </a>
                  <Button variant="outline" onClick={() => { navigator.clipboard.writeText(drawer.job.url); setToast('Copied!'); setTimeout(() => setToast(null), 2000) }}>
                    Copy URL
                  </Button>
                </div>

                {drawer.job.apply_reason && (
                  <div className="mb-3 p-3 rounded-lg text-sm border"
                    style={{
                      background: ['Apply Now','Apply Soon'].includes(drawer.job.action) ? 'rgba(34,197,94,0.08)' : drawer.job.action === 'Consider' ? 'rgba(234,179,8,0.08)' : 'rgba(239,68,68,0.08)',
                      borderColor: ['Apply Now','Apply Soon'].includes(drawer.job.action) ? 'rgba(34,197,94,0.2)' : drawer.job.action === 'Consider' ? 'rgba(234,179,8,0.2)' : 'rgba(239,68,68,0.2)',
                      color: ['Apply Now','Apply Soon'].includes(drawer.job.action) ? '#4ade80' : drawer.job.action === 'Consider' ? '#facc15' : '#f87171',
                    }}>
                    <div className="text-[0.6rem] uppercase tracking-wider font-semibold mb-1 opacity-70">Why {drawer.job.action || 'Apply/Skip'}</div>
                    {drawer.job.apply_reason}
                  </div>
                )}

                <Tabs value={drawerTab} onValueChange={setDrawerTab} className="mb-3">
                  <TabsList className="w-full justify-start">
                    <TabsTrigger value="details">Details</TabsTrigger>
                    <TabsTrigger value="structured">Structured</TabsTrigger>
                    <TabsTrigger value="summary">Summary</TabsTrigger>
                    <TabsTrigger value="resume">Resume</TabsTrigger>
                    <TabsTrigger value="cover">Cover Letter</TabsTrigger>
                  </TabsList>
                  {drawerTab === 'resume' && (
                    <div className="flex justify-end mt-2">
                      <Button variant={drawer.resume ? "outline" : "default"} size="sm" onClick={() => generateResume(drawer.job.num)} disabled={generatingResume} className="gap-1.5 h-7 text-xs">
                        {generatingResume ? <Spinner className="w-3 h-3 animate-spin" /> : <Repeat className="w-3 h-3" />}
                        {generatingResume ? 'Generating...' : drawer.resume ? 'Regenerate Resume' : 'Generate Resume'}
                      </Button>
                    </div>
                  )}
                  {drawerTab === 'cover' && (
                    <div className="flex justify-end mt-2">
                      <Button variant={drawer.coverLetter ? "outline" : "default"} size="sm" onClick={() => generateCover(drawer.job.num)} disabled={generatingCover} className="gap-1.5 h-7 text-xs">
                        {generatingCover ? <Spinner className="w-3 h-3 animate-spin" /> : <Repeat className="w-3 h-3" />}
                        {generatingCover ? 'Generating...' : drawer.coverLetter ? 'Regenerate Cover' : 'Generate Cover Letter'}
                      </Button>
                    </div>
                  )}
                </Tabs>

                {drawerTab === 'details' && (() => {
                  let sd = null; try { sd = drawer.job.structured_description ? JSON.parse(drawer.job.structured_description) : null } catch {}
                  return (
                    <div>
                      <ul className="text-sm space-y-1 mb-3 text-muted-foreground">
                        <li><b className="text-foreground">Salary:</b> {drawer.job.salary}</li>
                        {drawer.job.company_url && <li><b className="text-foreground">Company Website:</b> <a href={drawer.job.company_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{drawer.job.company_url}</a></li>}
                        <li><b className="text-foreground">Industry:</b> {drawer.job.industry}</li>
                        <li><b className="text-foreground">Domain:</b> {drawer.job.domain}</li>
                        <li><b className="text-foreground">Posted:</b> {drawer.job.posted}</li>
                        {drawer.job.adv_at && <li><b className="text-foreground">Listed:</b> {new Date(drawer.job.adv_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</li>}
                        {drawer.job.see_at && <li><b className="text-foreground">Seen:</b> {new Date(drawer.job.see_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</li>}
                        <li><b className="text-foreground">Applicants:</b> {drawer.job.applicants}</li>
                        <li><b className="text-foreground">Visa:</b> {drawer.job.visa}</li>
                        <li><b className="text-foreground">Work Type:</b> {drawer.job.work_type}</li>
                        {sd?.company_size && <li><b className="text-foreground">Company Size:</b> {sd.company_size}</li>}
                      </ul>
                      {sd?.responsibilities?.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Key Responsibilities</h4>
                          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul>
                        </div>
                      )}
                      {sd?.requirements?.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Requirements</h4>
                          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3.5 h-3.5 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul>
                        </div>
                      )}
                      {sd?.nice_to_have?.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Nice to Have</h4>
                          <ul className="text-sm space-y-1">{sd.nice_to_have.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Star className="w-3.5 h-3.5 shrink-0 mt-0.5 text-yellow-500" /><span>{r}</span></li>)}</ul>
                        </div>
                      )}
                      {sd?.benefits?.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Benefits</h4>
                          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3.5 h-3.5 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul>
                        </div>
                      )}
                      {sd?.visa_reason && (
                        <div className="mb-3">
                          <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Visa Assessment</h4>
                          <p className="text-sm flex items-start gap-2 text-muted-foreground"><Shield className="w-3.5 h-3.5 shrink-0 mt-0.5 text-primary" /><span>{sd.visa_reason}</span></p>
                        </div>
                      )}
                      <div className="mb-3">
                        <h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Analysis</h4>
                        <p className="text-sm text-muted-foreground">{drawer.job.notes}</p>
                      </div>
                    </div>
                  )
                })()}

                {drawerTab === 'structured' && (() => {
                  let sd = null; try { sd = drawer.job.structured_description ? JSON.parse(drawer.job.structured_description) : null } catch {}
                  if (!sd) return <div className="text-xs py-4 text-center text-muted-foreground">No structured data available</div>
                  return (
                    <div>
                      {sd.requirements?.length > 0 && (
                        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Requirements</h4>
                          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3 h-3 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul></div>
                      )}
                      {sd.responsibilities?.length > 0 && (
                        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Responsibilities</h4>
                          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3 h-3 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul></div>
                      )}
                      {sd.benefits?.length > 0 && (
                        <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Benefits</h4>
                          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3 h-3 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul></div>
                      )}
                    </div>
                  )
                })()}

                {drawerTab === 'summary' && drawer.summary && (
                  <div>
                    <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Summary</h4><p className="text-sm text-muted-foreground">{drawer.summary.summary}</p></div>
                    <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Stack Required</h4><p className="text-sm text-muted-foreground">{drawer.summary.stack}</p></div>
                    <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Resume Fit</h4><p className="text-sm text-muted-foreground">{drawer.summary.resumeFit}</p></div>
                    <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1 text-primary">Note</h4>
                      <p className="text-sm font-semibold" style={{ color: ['A','A+','A++'].includes(drawer.summary.score) ? '#22c55e' : ['B','C'].includes(drawer.summary.score) ? '#eab308' : '#ef4444' }}>{drawer.summary.note}</p></div>
                  </div>
                )}

                {drawerTab === 'resume' && (
                  <div>
                    {drawer.resume && <ResumePreview html={drawer.resume.content} />}
                    {!drawer.resume && (
                      <div className="flex flex-col items-center justify-center py-12 gap-4">
                        <FileText className="w-12 h-12 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">No tailored resume generated yet</p>
                      </div>
                    )}
                  </div>
                )}

                {drawerTab === 'cover' && (
                  <div>
                    {drawer.coverLetter && <ResumePreview html={drawer.coverLetter.content} />}
                    {!drawer.coverLetter && (
                      <div className="flex flex-col items-center justify-center py-12 gap-4">
                        <FileText className="w-12 h-12 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">No cover letter generated yet</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )
          })()}
        </SheetContent>
      </Sheet>

      {/* Confirm Dialog */}
      <AlertDialog open={!!confirmDialog} onOpenChange={(open) => { if (!open && confirmDialog) { confirmDialog.resolve(false); setConfirmDialog(null) } }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmDialog?.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmDialog?.message}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => { confirmDialog?.resolve(false); setConfirmDialog(null) }}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => { confirmDialog?.resolve(true); setConfirmDialog(null) }}
              className={cn(confirmDialog?.variant === 'warning' ? 'bg-yellow-500 hover:bg-yellow-600' : confirmDialog?.variant === 'info' ? '' : 'bg-destructive hover:bg-destructive/90')}>
              {confirmDialog?.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Duplicate Job Dialog */}
      <Dialog open={!!duplicateJob} onOpenChange={(open) => !open && setDuplicateJob(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Warning className="w-5 h-5 text-yellow-500" />
              Job Already Exists
            </DialogTitle>
            <DialogDescription>How would you like to update this job?</DialogDescription>
          </DialogHeader>
          <Card className="p-3 bg-muted">
            <div className="text-sm font-bold">#{duplicateJob?.num} {duplicateJob?.company}</div>
            <div className="text-xs mt-1 text-muted-foreground">
              Score: <span className="font-bold" style={{ color: ['A','A+','A++'].includes(duplicateJob?.score) ? '#22c55e' : ['B','C'].includes(duplicateJob?.score) ? '#eab308' : '#ef4444' }}>{duplicateJob?.score}</span>
              {' · '}
              Match: <span className="font-bold text-primary">{duplicateJob?.match}</span>
            </div>
          </Card>
          <DialogFooter className="flex-row gap-2">
            <Button className="flex-1 gap-1" onClick={async () => { await fetch(`${API}/jobs/${duplicateJob.num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }}>
              <TrendUp className="w-3.5 h-3.5" /> Rescore
            </Button>
            <Button variant="outline" className="flex-1 gap-1" onClick={async () => { await fetch(`${API}/jobs/${duplicateJob.num}/requeue`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }}>
              <Repeat className="w-3.5 h-3.5" /> Reprocess
            </Button>
            <Button variant="ghost" onClick={() => setDuplicateJob(null)}>Cancel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Workflow Terminal Drawer */}
      <Sheet open={!!workflowDrawer} onOpenChange={(open) => { if (!open) { workflowWs.current?.close(); setWorkflowDrawer(null); setWorkflowLogs([]) } }}>
        <SheetContent className="w-[min(600px,92vw)] sm:max-w-[600px] flex flex-col p-0">
          <SheetHeader className="px-4 py-2.5 border-b">
            <div className="flex items-center gap-2">
              <span className="text-sm">💻</span>
              <SheetTitle className="text-sm">Workflow Terminal</SheetTitle>
              <Badge variant="secondary" className="text-[0.6rem]">{workflowDrawer?.company || 'Job'} #{workflowDrawer?.job_num || '?'}</Badge>
              {workflowDrawer?.status === 'processing' && (
                <Badge variant="default" className="text-[0.55rem] animate-pulse">● LIVE</Badge>
              )}
            </div>
          </SheetHeader>

          {/* Step progress */}
          <div className="px-4 py-2 flex gap-1 border-b bg-muted overflow-x-auto">
            {['fetch', 'validate', 'extract_raw', 'extract_struct', 'summary', 'resume', 'score', 'done'].map((s, i) => {
              const stepVal = workflowDrawer?.[`step_${s}`]
              const isDone = stepVal === 1
              const isActive = !isDone && workflowLogs.some(l => l.step === s)
              return (
                <div key={s} className="flex items-center gap-0.5 shrink-0">
                  <div className={cn(
                    "w-4 h-4 rounded-full flex items-center justify-center text-[0.45rem] font-bold transition-all border",
                    isDone ? "bg-green-500 text-white border-green-500" :
                    isActive ? "bg-primary text-primary-foreground border-primary" :
                    "bg-background text-muted-foreground border-border"
                  )}>
                    {isDone ? <Check className="w-2.5 h-2.5" /> : isActive ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : i + 1}
                  </div>
                  {i < 7 && <div className={cn("h-[1px] w-3 rounded-full", isDone ? "bg-green-500" : "bg-border")} />}
                </div>
              )
            })}
          </div>

          {/* Terminal output */}
          <ScrollArea ref={workflowEndRef} className="flex-1 font-mono text-[0.7rem] leading-relaxed bg-[#0d1117] text-[#c9d1d9]">
            <div className="p-3">
              {workflowLogs.length === 0 && (
                <div className="text-center py-12 text-[#484f58]">
                  <Spinner className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <div>Waiting for workflow output...</div>
                  <div className="text-[0.6rem] mt-1 text-[#21262d]">WebSocket connecting to stream server...</div>
                </div>
              )}
              {workflowLogs.map((log, i) => {
                const isCmd = log.step === 'cmd'; const isOut = log.step === 'out'; const isErr = log.step === 'err'
                const isMimo = log.step === 'mimo'; const isStep = log.step === 'step'; const isError = log.step === 'error'; const isDone = log.step === 'done'
                return (
                  <div key={i} className={cn("mb-0.5", isError || isErr ? "bg-red-500/10 -mx-3 px-3 py-0.5 rounded" : "")}>
                    {isCmd ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#58a6ff]">$</span><span className="text-[#58a6ff]">{log.msg}</span></div> :
                     isOut ? <div className="pl-[70px] text-[#8b949e]">{log.msg}</div> :
                     isErr ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#f85149]">✗</span><span className="text-[#f85149]">{log.msg}</span></div> :
                     <div className="flex gap-2">
                       <span className="text-[#484f58] shrink-0">{log.ts}</span>
                       {!isMimo && !isStep && <span className="font-bold uppercase shrink-0 text-[#58a6ff]" style={{ minWidth: '50px' }}>[{log.step}]</span>}
                       <span className={isMimo ? 'whitespace-pre-wrap' : ''} style={{ color: isError ? '#f85149' : isDone || isStep ? '#3fb950' : '#c9d1d9' }}>
                         {isStep ? <><span className="text-[#3fb950]">✓</span> {log.msg}</> : isDone ? <><Confetti className="w-4 h-4 inline text-[#3fb950]" /> {log.msg}</> : log.msg}
                       </span>
                     </div>}
                  </div>
                )
              })}
              {workflowDrawer?.status === 'processing' && (
                <div className="flex gap-2 mt-1">
                  <span className="text-[#484f58]">{new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                  <span className="text-[#22c55e]">$</span>
                  <span className="animate-pulse text-[#22c55e]">█</span>
                </div>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[300] px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all duration-300 bg-green-500">
          {toast}
        </div>
      )}
    </div>
  )
}

export default App
