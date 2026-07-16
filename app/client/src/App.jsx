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
  CurrencyDollar, UsersFour, HourglassHigh, Handshake, Student, Lightbulb, GraduationCap
} from '@phosphor-icons/react'

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
function EmojiIcon({ emoji, className = 'w-4 h-4', style }) {
  return EMOJI_ICON_MAP[emoji] || <span className={className}>{emoji}</span>
}

const API = '/api'

const getScoreColor = s => s >= 75 ? 'text-green-500' : s >= 50 ? 'text-yellow-500' : 'text-red-500'
const getMatchClass = m => m === 'High' ? 'bg-green-500/15 text-green-500' : m === 'Medium' ? 'bg-yellow-500/15 text-yellow-500' : 'bg-red-500/15 text-red-500'

const CITY_COLORS = {
  'Berlin': { bg: 'rgba(239,68,68,0.15)', text: '#ef4444' },
  'Hamburg': { bg: 'rgba(249,115,22,0.15)', text: '#f97316' },
  'Munich': { bg: 'rgba(234,179,8,0.15)', text: '#eab308' },
  'Germany': { bg: 'rgba(34,197,94,0.15)', text: '#22c55e' },
  'Heidelberg': { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6' },
}
const DEFAULT_CITY_COLOR = { bg: 'var(--surface2)', text: 'var(--text-dim)' }

const VISA_STYLES = {
  'BEST': { bg: 'rgba(34,197,94,0.2)', text: '#22c55e', label: 'BEST' },
  'Strong': { bg: 'rgba(34,197,94,0.12)', text: '#4ade80', label: 'Strong' },
  'Good': { bg: 'rgba(234,179,8,0.12)', text: '#facc15', label: 'Good' },
  'Moderate': { bg: 'rgba(249,115,22,0.12)', text: '#fb923c', label: 'Moderate' },
  'High': { bg: 'rgba(59,130,246,0.12)', text: '#60a5fa', label: 'High' },
  'Uncertain': { bg: 'var(--surface2)', text: 'var(--text-dim)', label: '?' },
  'N/A': { bg: 'var(--surface2)', text: 'var(--text-dim)', label: 'N/A' },
}

function MultiSelect({ value, onChange, options, placeholder, alignRight, icon }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const toggle = (v) => {
    onChange(value.includes(v) ? value.filter(x => x !== v) : [...value, v])
  }
  const hasValue = value.length > 0
  return (
    <div ref={ref} className="relative flex-shrink-0">
      <button onClick={() => setOpen(!open)}
        className="px-1.5 py-0.5 rounded border text-[0.6rem] flex items-center gap-1 whitespace-nowrap transition"
        style={{background: hasValue ? 'rgba(99,102,241,0.15)' : 'var(--surface2)', borderColor: open ? 'var(--accent)' : hasValue ? 'var(--accent)' : 'var(--border)', color: hasValue ? 'var(--accent)' : 'var(--text-dim)'}}>
        {icon && <span className="flex-shrink-0" style={{color: hasValue ? 'var(--accent)' : 'var(--text-dim)'}}>{icon}</span>}
        {hasValue ? `${value.length} sel` : placeholder}
        <CaretDown className="w-2 h-2 flex-shrink-0" />
      </button>
      {open && (
        <div className={`absolute z-50 mt-1 w-40 rounded-lg border shadow-lg max-h-40 overflow-y-auto ${alignRight ? 'right-0' : 'left-0'}`}
          style={{background:'var(--surface)',borderColor:'var(--border)'}}>
          {options.map(o => {
            const checked = value.includes(o.value)
            return (
              <label key={o.value} className="flex items-center gap-1.5 px-2 py-1 text-[0.6rem] cursor-pointer transition"
                style={{background: checked ? 'rgba(99,102,241,0.1)' : 'transparent', color:'var(--text)'}}>
                <input type="checkbox" checked={checked} onChange={() => toggle(o.value)}
                  className="rounded w-3 h-3" style={{accentColor:'var(--accent)'}} />
                {o.icon && <span>{o.icon}</span>}
                <span style={{fontWeight: checked ? 600 : 400}}>{o.label}</span>
              </label>
            )
          })}
        </div>
      )}
    </div>
  )
}

function App() {
  const [jobs, setJobs] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [resumes, setResumes] = useState([])
  const [cities, setCities] = useState([])
  const [tab, setTab] = useState(() => {
    const hash = window.location.hash.replace('#', '')
    return hash || 'scoreboard'
  })
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
  const [maximizedCol, setMaximizedCol] = useState(null) // null | 'queue' | 'processing' | 'failed' | 'done'
  const [dragOverCol, setDragOverCol] = useState(null)
  const JOBS_PAGE_SIZE = 30
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const jobsScrollRef = useRef(null)
  const jobsSentinelRef = useRef(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  const [preferences, setPreferences] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [dashboardSubTab, setDashboardSubTab] = useState('overview')

  useEffect(() => {
    Promise.all([
      fetch(`${API}/jobs?offset=0&limit=${JOBS_PAGE_SIZE}&sort_by=created_at&sort_dir=desc`).then(r => r.json()),
      fetch(`${API}/summaries`).then(r => r.json()),
      fetch(`${API}/resumes`).then(r => r.json()),
      fetch(`${API}/cities`).then(r => r.json()),
    ]).then(([jobsData, sums, res, cits]) => {
      setJobs(jobsData.jobs || [])
      setJobsTotal(jobsData.total || 0)
      setJobsPage(0)
      setSummaries(sums)
      setResumes(res)
      setCities(cits)
    })
    fetchPending()
    fetchPreferences()
    fetchAnalysis()
  }, [])

  const fetchPreferences = () => fetch(`${API}/preferences`).then(r => r.json()).then(setPreferences)
  const fetchAnalysis = () => {
    fetch(`${API}/analysis`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setAnalysis(data))
      .catch(() => {})
  }

  // SSE for real-time pending job updates + fallback polling
  // When a job finishes (status → 'done'), refresh jobs data so it appears in Processed column
  const seenDoneRef = useRef(new Set())
  const refreshJobs = () => {
    const params = new URLSearchParams()
    params.set('offset', '0')
    params.set('limit', String((jobsPage + 1) * JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy)
    params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => {
      setJobs(d.jobs || [])
      setJobsTotal(d.total || 0)
    })
  }

  const loadMoreJobs = useCallback(async () => {
    if (loadingMore) return
    const nextPage = jobsPage + 1
    const offset = nextPage * JOBS_PAGE_SIZE
    if (offset >= jobsTotal) return
    setLoadingMore(true)
    try {
      const params = new URLSearchParams()
      params.set('offset', String(offset))
      params.set('limit', String(JOBS_PAGE_SIZE))
      params.set('sort_by', sortBy)
      params.set('sort_dir', sortDir)
      if (filterCities.length) params.set('filter_cities', filterCities.join(','))
      if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
      if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
      if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
      if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
      if (filterTech) params.set('filter_tech', filterTech)
      const res = await fetch(`${API}/jobs?${params}`)
      const data = await res.json()
      setJobs(prev => [...prev, ...(data.jobs || [])])
      setJobsPage(nextPage)
    } finally {
      setLoadingMore(false)
    }
  }, [jobsPage, jobsTotal, loadingMore, sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech])

  useEffect(() => {
    let es
    const checkDone = (pendingList) => {
      const newlyDone = pendingList.filter(p => p.status === 'done' && !seenDoneRef.current.has(p.id))
      if (newlyDone.length > 0) {
        newlyDone.forEach(p => seenDoneRef.current.add(p.id))
        refreshJobs()
      }
    }
    const connect = () => {
      es = new EventSource(`${API}/pending/stream`)
      es.onmessage = (e) => { try { const list = JSON.parse(e.data); setPending(list); checkDone(list) } catch {} }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    // Fallback: poll every 5s in case SSE drops; also poll for rescoring updates
    const poll = setInterval(() => {
      fetchPending().then(checkDone)
      // Also refresh jobs to pick up rescoring completions
      refreshJobs()
    }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech])

  // Sync tab with URL hash
  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace('#', '')
      if (h && h !== tab) setTab(h)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

  // Infinite scroll: observe sentinel element at bottom of Processed column
  useEffect(() => {
    const sentinel = jobsSentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) loadMoreJobs()
    }, { threshold: 0.1 })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadMoreJobs])

  const fetchPending = () => fetch(`${API}/pending`).then(r => r.json()).then(list => { setPending(list); return list })

  const submitUrl = async () => {
    if (!urlInput.trim()) return
    setUrlError('')
    const rawUrl = urlInput.trim()

    setSubmitting(true)
    const res = await fetch(`${API}/pending`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: rawUrl, source: 'web' })
    })
    const data = await res.json()

    // If URL already exists in DB, show choice dialog
    if (res.ok && data.status === 'exists') {
      setDuplicateJob(data)
      setUrlInput(''); setSubmitting(false)
      return
    }

    if (!res.ok) {
      setUrlError(data.error || 'Failed to add URL')
      setSubmitting(false)
      return
    }
    setUrlInput(''); setSubmitting(false); fetchPending()
    // Process immediately if checkbox is on
    if (processImmediately && data.id) {
      await processPending(data.id)
    }
  }

  const deletePending = async (id) => {
    await fetch(`${API}/pending/${id}`, { method: 'DELETE' }); fetchPending()
  }

  const processPending = async (id) => {
    await fetch(`${API}/pending/${id}/process`, { method: 'POST' }); fetchPending()
  }

  const resetPending = async (id) => {
    await fetch(`${API}/pending/${id}/reset`, { method: 'PUT' }); fetchPending()
  }

  const pausePending = async (id) => {
    await fetch(`${API}/pending/${id}/pause`, { method: 'PUT' }); fetchPending()
  }

  const rescoreJob = async (num) => {
    await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs()
  }

  const rescoreAll = async () => {
    await fetch(`${API}/jobs/rescore-all`, { method: 'POST' }); fetchPending(); refreshJobs()
  }

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => {
      setConfirmDialog({ title, message, confirmLabel, variant, resolve })
    })
  }

  const reprocessAll = async () => {
    const ok = await showConfirm('Reprocess All', 'Reprocess ALL jobs? Every job will be re-queued for full processing from scratch.', 'Reprocess All')
    if (!ok) return
    await fetch(`${API}/jobs/reprocess-all`, { method: 'POST' }); fetchPending()
  }

  const deleteJob = async (num) => {
    const ok = await showConfirm('Hide Job', `Hide job #${num}? It can be restored later.`, 'Hide')
    if (!ok) return
    await fetch(`${API}/jobs/${num}`, { method: 'DELETE' })
    refreshJobs()
  }

  const requeueJob = async (num) => {
    const ok = await showConfirm('Reprocess Job', `Reprocess job #${num} from scratch? The current version will be permanently deleted.`, 'Reprocess')
    if (!ok) return
    await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' })
    fetchPending()
    refreshJobs()
  }

  // Drag-and-drop state
  const [dragId, setDragId] = useState(null)
  const [workflowDrawer, setWorkflowDrawer] = useState(null) // pending job for workflow drawer
  const [workflowLogs, setWorkflowLogs] = useState([]) // streaming logs
  const workflowWs = useRef(null)
  const workflowEndRef = useRef(null)

  // WebSocket for workflow streaming
  const connectWorkflowWs = (pid) => {
    if (workflowWs.current) workflowWs.current.close()
    const ws = new WebSocket(`ws://${window.location.hostname}:8765`)
    workflowWs.current = ws
    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'watch', pid }))
    }
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt.type === 'state') {
          setWorkflowLogs(evt.logs || [])
        } else if (evt.type === 'tool_output') {
          const stream = evt.stream
          const tool = evt.tool || ''
          const data = evt.data || ''
          if (stream === 'input') {
            setWorkflowLogs(prev => [...prev, { step: 'cmd', msg: data, ts: evt.ts }])
          } else if (stream === 'output') {
            // Split multi-line output into separate log lines
            data.split('\n').forEach(line => {
              if (line.trim()) setWorkflowLogs(prev => [...prev, { step: 'out', msg: line, ts: evt.ts }])
            })
          } else if (stream === 'error') {
            setWorkflowLogs(prev => [...prev, { step: 'err', msg: data, ts: evt.ts }])
          } else if (stream === 'text') {
            setWorkflowLogs(prev => [...prev, { step: 'mimo', msg: data, ts: evt.ts }])
          }
        } else if (evt.type === 'mimo_event') {
          const mimoEvt = evt.event
          if (mimoEvt.type === 'step_finish') {
            const reason = mimoEvt.part?.reason || ''
            const tokens = mimoEvt.part?.tokens?.total || 0
            setWorkflowLogs(prev => [...prev, { step: 'step', msg: `Step finished: ${reason} (${tokens} tokens)`, ts: evt.ts }])
          }
        } else if (evt.type === 'mimo_raw') {
          setWorkflowLogs(prev => [...prev, { step: 'raw', msg: evt.line, ts: evt.ts }])
        } else if (evt.type === 'job_info') {
          // Update pending item with fetched title/company
          setPending(prev => prev.map(p => p.id === evt.pid ? { ...p, company: evt.company || p.company, title: evt.title } : p))
        } else if (evt.type === 'step') {
          setWorkflowLogs(prev => [...prev, { step: evt.step, msg: `[${evt.status}]`, ts: evt.ts }])
        } else if (evt.type === 'complete') {
          setWorkflowLogs(prev => [...prev, { step: 'done', msg: `Complete: ${evt.company} #${evt.num}`, ts: evt.ts }])
        } else if (evt.type === 'error') {
          setWorkflowLogs(prev => [...prev, { step: 'error', msg: evt.msg, ts: evt.ts }])
        }
      } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {}
  }

  // Auto-scroll to bottom
  useEffect(() => {
    workflowEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [workflowLogs])

  // Open workflow drawer with WebSocket connection
  const openWorkflow = (item) => {
    setWorkflowLogs([])
    setWorkflowDrawer(item)
    connectWorkflowWs(item.id)
  }



  // Parse locations for each job (handle both JSON array and legacy string)
  const jobsWithLocations = useMemo(() => {
    if (!jobs) return []
    return jobs.map(j => {
      let locations = []
      if (j.locations) {
        try {
          locations = typeof j.locations === 'string' ? JSON.parse(j.locations) : j.locations
        } catch { locations = [] }
      }
      if (!locations.length && j.location) locations = [j.location]
      return { ...j, parsedLocations: locations }
    })
  }, [jobs])

  const allCities = jobsWithLocations ? [...new Set(jobsWithLocations.flatMap(j => j.parsedLocations))].sort() : []
  const allCompanies = jobsWithLocations ? [...new Set(jobsWithLocations.map(j => j.company))].sort() : []

  // Server-side filtering: filteredJobs = jobs directly (server applies filters)
  // We still compute filteredJobs for the sort/display pipeline
  const filteredJobs = useMemo(() => {
    if (!jobsWithLocations) return []
    let r = [...jobsWithLocations]
    r.sort((a, b) => {
      if (sortBy === 'score') return sortDir === 'desc' ? b.score - a.score : a.score - b.score
      if (sortBy === 'num') return sortDir === 'desc' ? b.num - a.num : a.num - b.num
      if (sortBy === 'company') return sortDir === 'desc' ? b.company.localeCompare(a.company) : a.company.localeCompare(b.company)
      if (sortBy === 'location') return sortDir === 'desc' ? b.location.localeCompare(a.location) : a.location.localeCompare(b.location)
      if (sortBy === 'applicants') {
        const aVal = parseInt(String(a.applicants).replace(/\D/g,'')) || 999
        const bVal = parseInt(String(b.applicants).replace(/\D/g,'')) || 999
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      if (sortBy === 'created_at') {
        const aVal = a.created_at ? new Date(a.created_at).getTime() : 0
        const bVal = b.created_at ? new Date(b.created_at).getTime() : 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      if (sortBy === 'posted_at') {
        const aVal = a.posted_at ? new Date(a.posted_at).getTime() : 0
        const bVal = b.posted_at ? new Date(b.posted_at).getTime() : 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      return 0
    })
    return r
  }, [jobsWithLocations, sortBy, sortDir])

  const sorted = jobs ? [...jobs].sort((a, b) => b.score - a.score) : []
  const activeFilterCount = filterCities.length + filterCompanies.length + filterMatches.length + filterWorkTypes.length + filterEmploymentTypes.length + (filterTech ? 1 : 0)

  const openDrawer = (num) => {
    if (!jobs) return
    const j = jobs.find(x => x.num === num)
    const s = summaries?.find(x => x.num === num)
    const r = resumes?.find(x => x.id !== 'original' && j.company.toLowerCase().includes(x.company.split(' ')[0].toLowerCase().replace(/[()]/g, '')))
    setDrawer({ job: j, summary: s, resume: r }); setDrawerTab('details')
  }

  const toggleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortBy(field); setSortDir('desc') }
  }

  const clearFilters = () => {
    setFilterCities([]); setFilterCompanies([]); setFilterTech(''); setFilterMatches([]); setFilterWorkTypes([]); setFilterEmploymentTypes([])
  }

  // Re-fetch from server when filters or sort change
  const filterChangeRef = useRef(false)
  useEffect(() => {
    if (!filterChangeRef.current) { filterChangeRef.current = true; return }
    setJobsPage(0)
    const params = new URLSearchParams()
    params.set('offset', '0')
    params.set('limit', String(JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy)
    params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => {
      setJobs(d.jobs || [])
      setJobsTotal(d.total || 0)
    })
  }, [sortBy, sortDir, filterCities, filterCompanies, filterTech, filterMatches, filterWorkTypes, filterEmploymentTypes])

  const switchTab = (t) => {
    setTab(t)
    window.location.hash = t
  }

  const tabs = [
    { id: 'scoreboard', icon: <Briefcase className="w-4 h-4" />, label: 'Jobs', badge: jobsTotal, section: 'jobs' },
    { id: 'dashboard', icon: <ChartBar className="w-4 h-4" />, label: 'Dashboard', section: 'analysis' },
    { id: 'preferences', icon: <Gear className="w-4 h-4" />, label: 'Preferences', section: 'settings' },
  ]

  const dashboardTabs = [
    { id: 'overview', icon: <ChartBar className="w-4 h-4" />, label: 'Overview' },
    { id: 'strategy', icon: <Target className="w-4 h-4" />, label: 'Strategy' },
    { id: 'skills', icon: <Brain className="w-4 h-4" />, label: 'Skills' },
  ]

  const [refreshing, setRefreshing] = useState({})

  const refreshAnalysis = async () => {
    setRefreshing(r => ({...r, analysis: true}))
    await fetch(`${API}/refresh/analysis`, { method: 'POST' })
    refreshJobs()
    fetchAnalysis()
    setRefreshing(r => ({...r, analysis: false}))
  }

  if (jobs === null) return <div className="flex items-center justify-center h-screen" style={{color:'var(--text-dim)'}}>Loading...</div>

  return (
    <div className="flex h-screen overflow-hidden" style={{background:'var(--bg)',color:'var(--text)'}}>
      <aside className="w-[170px] border-r flex flex-col pt-12" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
        <div className="px-3 py-2 text-xs uppercase tracking-wider" style={{color:'var(--text-dim)'}}>Jobs</div>
        {tabs.filter(t => t.section === 'jobs').map(t => (
          <button key={t.id} onClick={() => switchTab(t.id)}
            className={`flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition ${tab===t.id ? 'border-l-[var(--accent)] font-semibold' : 'border-l-transparent'}`}
            style={{color: tab===t.id ? 'var(--accent)' : 'var(--text-dim)'}}>
            <span>{t.icon}</span><span>{t.label}</span>
            {t.badge && <span className="ml-auto text-[0.55rem] font-bold px-1.5 py-0.5 rounded-md text-white" style={{background:'var(--accent)'}}>{t.badge}</span>}
          </button>
        ))}
        <div className="px-3 py-2 mt-2 text-xs uppercase tracking-wider" style={{color:'var(--text-dim)'}}>Analysis</div>
        {tabs.filter(t => t.section === 'analysis').map(t => (
          <button key={t.id} onClick={() => switchTab(t.id)}
            className={`flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition ${tab===t.id ? 'border-l-[var(--accent)] font-semibold' : 'border-l-transparent'}`}
            style={{color: tab===t.id ? 'var(--accent)' : 'var(--text-dim)'}}>
            <span>{t.icon}</span><span>{t.label}</span>
          </button>
        ))}
        <div className="px-3 py-2 mt-2 text-xs uppercase tracking-wider" style={{color:'var(--text-dim)'}}>Settings</div>
        {tabs.filter(t => t.section === 'settings').map(t => (
          <button key={t.id} onClick={() => switchTab(t.id)}
            className={`flex items-center gap-2 px-3 py-2 text-sm border-l-3 transition ${tab===t.id ? 'border-l-[var(--accent)] font-semibold' : 'border-l-transparent'}`}
            style={{color: tab===t.id ? 'var(--accent)' : 'var(--text-dim)'}}>
            <span>{t.icon}</span><span>{t.label}</span>
          </button>
        ))}
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-12 border-b flex items-center px-4 gap-6 shrink-0 fixed top-0 left-[170px] right-0 z-50" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
          <span className="font-extrabold text-sm bg-gradient-to-r from-[var(--accent)] to-[var(--purple)] bg-clip-text text-transparent">JS</span>
          <div className="flex gap-4 text-sm" style={{color:'var(--text-dim)'}}>
            <span><b className="text-[var(--text)]">{jobsTotal}</b> Jobs</span>
            <span><b className="text-green-500">{jobs.filter(j=>j.match==='High').length}</b> High</span>
            <span><b className="text-purple-500">{sorted[0]?.score}</b> Top</span>
            <span><b className="text-cyan-500">{resumes.filter(r=>r.id!=='original').length}</b> Resumes</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs" style={{color:'var(--text-dim)'}}>July 15, 2026</span>
            <button onClick={() => setTheme(t => t==='dark'?'light':'dark')}
              className="w-8 h-8 rounded-lg border flex items-center justify-center text-sm transition hover:border-[var(--accent)]"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>
              {theme==='dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">

            {/* === SCOREBOARD (Kanban with maximize + drag-drop) === */}
            {tab === 'scoreboard' && (() => {
              const qCount = pending.filter(p=>p.status==='queued').length
              const pCount = pending.filter(p=>p.status!=='done'&&p.status!=='failed'&&p.status!=='queued').length
              const fCount = pending.filter(p=>p.status==='failed').length
              const anyMax = maximizedCol !== null

              const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
              const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
              const handleDragLeave = () => { setDragOverCol(null) }
              const handleDrop = (e, colId) => {
                e.preventDefault(); setDragOverCol(null)
                if (!dragId) return
                if (colId === 'queue') resetPending(dragId)      // Processing → Queue
                else if (colId === 'processing') processPending(dragId)  // Queue → Processing
                setDragId(null)
              }

              const colConfigs = [
                { id:'queue', icon:<Clock className="w-4 h-4" />, label:'Queue', count:qCount, color:'#eab308', bg:'rgba(234,179,8,' },
                { id:'processing', icon:<Gear className="w-4 h-4" />, label:'Processing', count:pCount + fCount, color:'var(--accent)', bg:'rgba(99,102,241,' },
              ]

              return (
                <div className="flex gap-2 h-[calc(100vh-80px)]">
                  {/* Queue, Processing, Process Failed columns */}
                  {colConfigs.map(col => {
                    const isMax = maximizedCol === col.id
                    const isMin = anyMax && !isMax
                    const isDrop = dragOverCol === col.id
                    const autoCols = Math.min(5, Math.max(1, Math.ceil(Math.sqrt(col.count))))
                    const gridStyle = isMax ? {display:'grid',gridTemplateColumns:`repeat(${autoCols}, minmax(0, 1fr))`,gap:'0.5rem',alignContent:'start'} : {}
                    if (isMin) {
                      return (
                        <div key={col.id}
                          onClick={() => setMaximizedCol(col.id)}
                          className="w-[44px] flex flex-col items-center justify-center gap-2 rounded-lg cursor-pointer select-none transition-all duration-200 hover:opacity-80"
                          style={{background:`linear-gradient(180deg, ${col.bg}0.25), ${col.bg}0.08))`,border:`1px solid ${col.bg}0.3)`}}>
                          <span className="text-xl" style={{color:col.color}}>{col.icon}</span>
                          <span className="text-base font-black" style={{color:col.color}}>{col.count}</span>
                          <span className="text-[0.6rem] font-black uppercase tracking-wider" style={{color:col.color,writingMode:'vertical-rl',textOrientation:'mixed'}}>{col.label}</span>
                        </div>
                      )
                    }
                    return (
                      <div key={col.id}
                        className={`flex flex-col rounded-lg border overflow-hidden transition-all duration-200 ${isMax ? 'flex-1' : 'w-[280px]'}`}
                        style={{background:'var(--surface)',borderColor: isDrop ? col.color : 'var(--border)', boxShadow: isDrop ? `0 0 0 2px ${col.color}` : 'none'}}>
                        <div onClick={()=>setMaximizedCol(isMax ? null : col.id)}
                          className="px-2 py-1.5 flex items-center gap-1 shrink-0 cursor-pointer select-none transition hover:opacity-80"
                          style={{background:`linear-gradient(135deg, ${col.bg}0.12), ${col.bg}0.04))`,borderBottom:`1px solid ${col.bg}0.2)`}}>
                          <span className="text-sm" style={{color:col.color}}>{col.icon}</span>
                          <span className="font-bold text-xs" style={{color:col.color}}>{col.label}</span>
                          <span className="text-[0.5rem] font-bold px-1.5 py-0.5 rounded-full ml-auto" style={{background:`${col.bg}0.15)`,color:col.color}}>{col.count}</span>
                        </div>
                        {!isMin && (
                          <div className="flex-1 overflow-y-auto p-2"
                            style={isMax ? gridStyle : {display:'flex',flexDirection:'column',gap:'0.5rem'}}
                            onDragOver={e => handleDragOver(e, col.id)} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, col.id)}>
                            {col.id === 'queue' && !isMin && (
                              <div className={`rounded-lg border shrink-0 ${isMax ? 'p-3 col-span-full' : 'p-2'}`} style={{background:'var(--surface2)',borderColor:'var(--border)'}}>
                                <input type="url" value={urlInput} onChange={e => { setUrlInput(e.target.value); setUrlError('') }}
                                  onKeyDown={e => e.key === 'Enter' && submitUrl()}
                                  placeholder="Paste LinkedIn URL..."
                                  className={`w-full rounded border outline-none mb-1 focus:border-[var(--accent)] ${isMax ? 'px-3 py-2 text-sm' : 'px-2 py-1.5 text-xs'}`}
                                  style={{background:'var(--surface)',borderColor: urlError ? 'var(--red)' : 'var(--border)',color:'var(--text)'}} />
                                {urlError && <div className="text-[0.55rem] mb-1 px-0.5 flex items-center gap-1" style={{color:'var(--red)'}}><Warning className="w-3 h-3" /> {urlError}</div>}
                                <div className="flex items-center gap-2">
                                  <button onClick={submitUrl} disabled={submitting || !urlInput.trim()}
                                    className={`flex-1 rounded font-bold text-white transition disabled:opacity-50 ${isMax ? 'px-3 py-2 text-xs' : 'px-2 py-1.5 text-[0.6rem]'}`}
                                    style={{background:'var(--accent)'}}>{submitting ? '...' : processImmediately ? 'Add & Process' : 'Add'}</button>
                                  <label className="flex items-center gap-1 cursor-pointer shrink-0" title="Process immediately">
                                    <input type="checkbox" checked={processImmediately} onChange={e => setProcessImmediately(e.target.checked)}
                                      className="rounded w-3 h-3" style={{accentColor:'var(--accent)'}} />
                                  </label>
                                </div>
                              </div>
                            )}
                            {col.id === 'queue' && pending.filter(p=>p.status==='queued').map(p =>
                              <PendingItem key={p.id} item={p} onProcess={()=>processPending(p.id)} onDragStart={e=>handleDragStart(e,p.id)} onViewWorkflow={openWorkflow} />)}
                            {col.id === 'queue' && qCount === 0 && <div className="text-center py-6 text-[0.6rem]" style={{color:'var(--text-dim)'}}>No queued jobs</div>}

                            {col.id === 'processing' && pending.filter(p=>p.status!=='done'&&p.status!=='failed'&&p.status!=='queued').map(p =>
                              <PendingItem key={p.id} item={p} onDragStart={e=>handleDragStart(e,p.id)}
                                onProcess={()=>processPending(p.id)} onReset={()=>resetPending(p.id)} onPause={()=>pausePending(p.id)} onDelete={()=>deletePending(p.id)} onViewWorkflow={openWorkflow} />)}
                            {col.id === 'processing' && pCount === 0 && <div className="text-center py-4 text-[0.6rem]" style={{color:'var(--text-dim)'}}>Nothing processing</div>}
                            {col.id === 'processing' && fCount > 0 && (
                              <div className="mt-1 pt-2 border-t" style={{borderColor:'rgba(239,68,68,0.2)'}}>
                                <div className="flex items-center gap-1 mb-2 px-1">
                                  <X className="w-3 h-3" style={{color:'var(--red)'}} />
                                  <span className="text-[0.55rem] font-bold uppercase tracking-wider" style={{color:'var(--red)'}}>Failed ({fCount})</span>
                                </div>
                                {pending.filter(p=>p.status==='failed').map(p =>
                                  <PendingItem key={p.id} item={p} onDelete={()=>deletePending(p.id)} onProcess={()=>processPending(p.id)} onReset={()=>resetPending(p.id)} onViewWorkflow={openWorkflow} />)}
                              </div>
                            )}
                          </div>
                        )}
                        {/* Minimized: icon + count only */}
                        {isMin && (
                          <div className="flex-1 flex flex-col items-center justify-center gap-2 py-2">
                            <span className="text-lg">{col.icon}</span>
                            <span className="text-sm font-black" style={{color:col.color}}>{col.count}</span>
                            <span className="text-[0.4rem] font-bold uppercase tracking-wider" style={{color:col.color,writingMode:'vertical-rl',textOrientation:'mixed'}}>{col.label}</span>
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {/* Processed column — with auto inner cols when maximized */}
                  {(() => {
                    const isMax = maximizedCol === 'done'
                    const isMin = anyMax && !isMax
                    const autoCols = Math.min(5, Math.max(1, Math.ceil(Math.sqrt(filteredJobs.length))))
                    const gridStyle = isMax ? {display:'grid',gridTemplateColumns:`repeat(${autoCols}, minmax(0, 1fr))`,gap:'0.5rem',alignContent:'start'} : {}
                    if (isMin) {
                      return (
                        <div onClick={() => setMaximizedCol('done')}
                          className="w-[44px] flex flex-col items-center justify-center gap-2 rounded-lg cursor-pointer select-none transition-all duration-200 hover:opacity-80"
                          style={{background:'linear-gradient(180deg, rgba(34,197,94,0.25), rgba(34,197,94,0.08))',border:'1px solid rgba(34,197,94,0.3)'}}>
                          <CheckCircle className="w-5 h-5" style={{color:'#22c55e'}} />
                          <span className="text-base font-black" style={{color:'#22c55e'}}>{filteredJobs.length}/{jobsTotal}</span>
                          <span className="text-[0.6rem] font-black uppercase tracking-wider" style={{color:'#22c55e',writingMode:'vertical-rl',textOrientation:'mixed'}}>Processed</span>
                        </div>
                      )
                    }
                    return (
                      <div className={`flex flex-col rounded-lg border overflow-hidden transition-all duration-200 ${isMax ? 'flex-1' : 'w-[500px]'}`}
                        style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div onClick={()=>setMaximizedCol(isMax ? null : 'done')}
                          className="px-2 py-1.5 flex items-center gap-1 shrink-0 cursor-pointer select-none transition hover:opacity-80"
                          style={{background:'linear-gradient(135deg, rgba(34,197,94,0.12), rgba(34,197,94,0.04))',borderBottom:'1px solid rgba(34,197,94,0.2)'}}>
                          <CheckCircle className="w-4 h-4" style={{color:'#22c55e'}} />
                          <span className="font-bold text-xs" style={{color:'#22c55e'}}>Processed</span>
                          <span className="text-[0.5rem] font-bold px-1.5 py-0.5 rounded-full" style={{background:'rgba(34,197,94,0.15)',color:'#22c55e'}}>{filteredJobs.length}/{jobsTotal}</span>
                          <div className="flex items-center gap-0.5 ml-auto" onClick={e => e.stopPropagation()}>
                            <button onClick={()=>refreshJobs()} title="Refresh from server" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'#22c55e'}}><ArrowsClockwise className="w-3 h-3" /></button>
                            <button onClick={()=>rescoreAll()} title="Rescore all jobs" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--accent)'}}><TrendUp className="w-3 h-3" /></button>
                            <button onClick={()=>reprocessAll()} title="Reprocess all jobs from scratch" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--yellow)'}}><Repeat className="w-3 h-3" /></button>
                          </div>
                        </div>
                        <div ref={jobsScrollRef} className="flex-1 overflow-y-auto p-2">
                          {/* First row: Search */}
                          <div className="flex items-center gap-1 mb-2">
                            <div className="relative flex-1">
                              <input value={filterTech} onChange={e=>setFilterTech(e.target.value)}
                                placeholder="Search by role, company, stack, or notes..."
                                className="w-full px-2 py-1.5 rounded border text-xs transition"
                                style={{background: filterTech ? 'rgba(99,102,241,0.15)' : 'var(--surface2)', borderColor: filterTech ? 'var(--accent)' : 'var(--border)', color: filterTech ? 'var(--accent)' : 'var(--text-dim)'}} />
                              {filterTech && <button onClick={()=>setFilterTech('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-[0.55rem]" style={{color:'var(--text-dim)'}}>✕</button>}
                            </div>
                            {activeFilterCount > 0 && <button onClick={clearFilters} className="px-2 py-1 rounded text-[0.6rem] font-semibold transition hover:bg-red-500/20 whitespace-nowrap" style={{color:'var(--red)'}}>Clear all</button>}
                          </div>
                          {/* Second row: Sort on left, filters on right */}
                          <div className="flex items-center justify-between gap-2 mb-2">
                            {/* Sort dropdown */}
                            <div className="relative">
                              <select value={sortBy} onChange={e => { setSortBy(e.target.value); setSortDir(e.target.value === 'score' ? 'desc' : 'desc') }}
                                className="px-2 py-1 rounded border text-[0.6rem] appearance-none cursor-pointer transition"
                                style={{background:'var(--surface2)', borderColor:'var(--border)', color:'var(--text)'}}>
                                <option value="created_at">Newest first</option>
                                <option value="posted_at">Posted date</option>
                                <option value="score">Score</option>
                                <option value="applicants">Applicants</option>
                                <option value="company">Company</option>
                                <option value="location">Location</option>
                              </select>
                              <button onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}
                                className="ml-1 px-1.5 py-0.5 rounded border text-[0.6rem] transition"
                                style={{background:'var(--surface2)', borderColor:'var(--border)', color:'var(--text)'}}>
                                {sortDir === 'desc' ? '↓' : '↑'}
                              </button>
                            </div>
                            {/* Filters */}
                            <div className="flex items-center gap-1 flex-wrap justify-end">
                              <MultiSelect value={filterCities} onChange={setFilterCities} placeholder="City" icon={<MapPin className="w-3 h-3" />} options={allCities.map(c=>({value:c,label:c}))} />
                              <MultiSelect value={filterCompanies} onChange={setFilterCompanies} placeholder="Co" icon={<Buildings className="w-3 h-3" />} options={allCompanies.map(c=>({value:c,label:c}))} />
                              <MultiSelect value={filterMatches} onChange={setFilterMatches} placeholder="Match" icon={<Target className="w-3 h-3" />} options={[{value:'High',label:'High'},{value:'Medium',label:'Medium'},{value:'Low',label:'Low'}]} />
                              <MultiSelect value={filterWorkTypes} onChange={setFilterWorkTypes} placeholder="Work" icon={<HouseSimple className="w-3 h-3" />} options={[{value:'On-site',label:'On-site'},{value:'Remote',label:'Remote'},{value:'Hybrid',label:'Hybrid'}]} />
                              <MultiSelect value={filterEmploymentTypes} onChange={setFilterEmploymentTypes} placeholder="Emp" icon={<Briefcase className="w-3 h-3" />} options={[{value:'Full-time',label:'Full-time'},{value:'Part-time',label:'Part-time'},{value:'Contract',label:'Contract'},{value:'Internship',label:'Internship'},{value:'Temporary',label:'Temporary'}]} alignRight />
                            </div>
                          </div>
                          <div style={isMax ? gridStyle : {display:'grid',gridTemplateColumns:'repeat(2, minmax(0, 1fr))',gap:'0.5rem'}}>
                            {filteredJobs.map((j,i) => <JobCard key={j.num} job={j} rank={i+1} onClick={()=>openDrawer(j.num)} onRescore={rescoreJob} onDelete={deleteJob} onRequeue={requeueJob} onViewWorkflow={openWorkflow} />)}
                          </div>
                          {/* Sentinel for infinite scroll */}
                          <div ref={jobsSentinelRef} className="h-1" />
                          {loadingMore && <div className="text-center py-2 text-[0.6rem]" style={{color:'var(--text-dim)'}}>Loading more...</div>}
                          {!loadingMore && filteredJobs.length >= jobsTotal && filteredJobs.length > 0 && <div className="text-center py-2 text-[0.55rem]" style={{color:'var(--text-dim)',opacity:0.5}}>All {jobsTotal} jobs loaded</div>}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )
            })()}

            {/* === DASHBOARD (Unified with inner tabs) === */}
            {tab === 'dashboard' && (() => {
              // Get data from unified analysis
              const analysisData = analysis?.analysis || {}
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

              const highMatchJobs = jobs.filter(j => j.match === 'High')
              const applyNow = jobs.filter(j => j.score >= 75)
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
                  {/* Header with inner tabs and refresh */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <h2 className="text-xl font-extrabold">Dashboard</h2>
                      <div className="flex gap-1 p-1 rounded-lg" style={{background:'var(--surface2)'}}>
                        {dashboardTabs.map(t => (
                          <button key={t.id} onClick={() => setDashboardSubTab(t.id)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition`}
                            style={{background: dashboardSubTab === t.id ? 'var(--surface)' : 'transparent', color: dashboardSubTab === t.id ? 'var(--accent)' : 'var(--text-dim)', boxShadow: dashboardSubTab === t.id ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'}}>
                            <span>{t.icon}</span>
                            <span>{t.label}</span>
                          </button>
                        ))}
                      </div>
                      <p className="text-xs" style={{color:'var(--text-dim)'}}>
                        {analysis?.created_at && (
                          <span>Last updated: {new Date(analysis.created_at).toLocaleString()}</span>
                        )}
                      </p>
                    </div>
                    <button onClick={refreshAnalysis} disabled={refreshing.analysis}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition disabled:opacity-50"
                      style={{background: refreshing.analysis ? 'var(--surface2)' : 'var(--accent)', color: refreshing.analysis ? 'var(--text-dim)' : 'white'}}>
                      <ArrowsClockwise className={`w-4 h-4 ${refreshing.analysis ? 'animate-spin' : ''}`} />
                      {refreshing.analysis ? 'Updating...' : 'Refresh Analysis'}
                    </button>
                  </div>

                  {/* === OVERVIEW TAB === */}
                  {dashboardSubTab === 'overview' && (
                    <div className="space-y-5">
                      {/* Hero Stats */}
                      <div className="grid grid-cols-6 gap-3">
                        {[
                          {n: overview.totalJobs || jobs.length, l: 'Total Jobs', c: 'var(--accent)', icon: <Briefcase className="w-5 h-5" />},
                          {n: overview.highMatch || highMatchJobs.length, l: 'High Match', c: 'var(--green)', icon: <Target className="w-5 h-5" />},
                          {n: overview.applyNow || applyNow.length, l: 'Apply Now (75+)', c: 'var(--yellow)', icon: <Rocket className="w-5 h-5" />},
                          {n: overview.remoteJobs || remoteJobs.length, l: 'Remote', c: 'var(--cyan)', icon: <House className="w-5 h-5" />},
                          {n: overview.visaReady || visaReady.length, l: 'Visa Ready', c: 'var(--purple)', icon: <IdentificationCard className="w-5 h-5" />},
                          {n: resumes.filter(r => r.id !== 'original').length, l: 'Resumes', c: 'var(--accent)', icon: <FileText className="w-5 h-5" />},
                        ].map((s, i) => (
                          <div key={i} className="rounded-lg p-4 border transition hover:border-[var(--accent)]" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="mb-1" style={{color:s.c}}>{s.icon}</div>
                            <div className="text-2xl font-extrabold" style={{color:s.c}}>{s.n}</div>
                            <div className="text-[0.65rem] uppercase tracking-wider mt-0.5" style={{color:'var(--text-dim)'}}>{s.l}</div>
                          </div>
                        ))}
                      </div>

                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          {/* Apply Now */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Rocket className="w-5 h-5" style={{color:'var(--yellow)'}} />
                              <h3 className="font-extrabold text-sm">Apply Now — Score 75+</h3>
                              <span className="text-[0.6rem] px-2 py-0.5 rounded-full font-bold" style={{background:'rgba(34,197,94,0.15)', color:'var(--green)'}}>{applyNow.length} jobs</span>
                            </div>
                            {applyNow.length === 0 ? (
                              <div className="text-center py-6 text-xs" style={{color:'var(--text-dim)'}}>No jobs scored 75+ yet</div>
                            ) : (
                              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                                {applyNow.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                              </div>
                            )}
                          </div>

                          {/* High Match Jobs */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Target className="w-5 h-5" style={{color:'var(--green)'}} />
                              <h3 className="font-extrabold text-sm">High Match Jobs</h3>
                              <span className="text-[0.6rem] px-2 py-0.5 rounded-full font-bold" style={{background:'rgba(34,197,94,0.15)', color:'var(--green)'}}>{highMatchJobs.length} jobs</span>
                            </div>
                            {highMatchJobs.length === 0 ? (
                              <div className="text-center py-6 text-xs" style={{color:'var(--text-dim)'}}>No high match jobs</div>
                            ) : (
                              <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                                {highMatchJobs.slice(0, 6).map(j => <CompactJobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                              </div>
                            )}
                          </div>

                          {/* Skill-Job Fit (new) */}
                          {skillJobFit.length > 0 && (
                            <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                              <div className="flex items-center gap-2 mb-3">
                                <Link className="w-5 h-5" style={{color:'var(--accent)'}} />
                                <h3 className="font-extrabold text-sm">Skill-Job Fit Analysis</h3>
                              </div>
                              <div className="space-y-2">
                                {skillJobFit.slice(0, 8).map((item, i) => (
                                  <div key={i} className="flex items-center gap-3 text-xs p-2 rounded-lg hover:bg-[var(--surface2)] transition">
                                    <div className="w-24 font-semibold" style={{color:'var(--text)'}}>{item.skill}</div>
                                    <div className="flex-1 h-2 rounded-full" style={{background:'var(--surface2)'}}>
                                      <div className="h-full rounded-full" style={{width:`${item.fitScore}%`, background: item.fitScore >= 70 ? 'var(--green)' : item.fitScore >= 40 ? 'var(--yellow)' : 'var(--red)'}} />
                                    </div>
                                    <div className="w-12 text-right font-bold" style={{color:'var(--accent)'}}>{item.fitScore}%</div>
                                    <div className="w-20 text-right" style={{color:'var(--text-dim)'}}>{item.jobsRequiring}/{overview.totalJobs || jobs.length}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="space-y-4">
                          {/* Cities */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Globe className="w-5 h-5" style={{color:'var(--accent)'}} />
                              <h3 className="font-extrabold text-sm">Cities</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              {cities?.slice(0, 6).map((c, i) => (
                                <div key={i} className="rounded-lg p-2 text-center border transition hover:border-[var(--accent)]" style={{background:'var(--surface2)', borderColor:'var(--border)'}}>
                                  <div className="mb-0.5" style={{color:'var(--accent)'}}><EmojiIcon emoji={c.icon} /></div>
                                  <div className="font-bold text-xs">{c.name}</div>
                                  <div className="text-[0.55rem]" style={{color:'var(--text-dim)'}}>{c.info}</div>
                                  <div className="text-[0.55rem] font-semibold" style={{color:'var(--accent)'}}>{c.jobs}</div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Visa Companies */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <IdentificationCard className="w-5 h-5" style={{color:'var(--purple)'}} />
                              <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
                            </div>
                            {visaCompanies.length > 0 ? (
                              <div className="space-y-1.5">
                                {visaCompanies.slice(0, 6).map((j, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{j.title || j.company}</span>
                                    <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(34,197,94,0.15)', color:'var(--green)'}}>{j.description || j.visa}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No visa data yet</div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* === STRATEGY TAB === */}
                  {dashboardSubTab === 'strategy' && (
                    <div className="space-y-5">
                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          {/* Strategy Guide */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Clipboard className="w-5 h-5" style={{color:'var(--accent)'}} />
                              <h3 className="font-extrabold text-sm">Strategy Guide</h3>
                              {strategy.length === 0 && <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)', color:'var(--text-dim)'}}>Processing...</span>}
                            </div>
                            <div className="space-y-2">
                              {strategy.map((g, i) => (
                                <div key={i} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-[var(--surface2)]" style={{borderLeft:'2px solid var(--accent)'}}>
                                  <span className="shrink-0" style={{color:'var(--accent)'}}><EmojiIcon emoji={g.icon} /></span>
                                  <div>
                                    <div className="font-bold text-xs">{g.title}</div>
                                    <div className="text-[0.6rem]" style={{color:'var(--text-dim)'}}>{g.description}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Apply Urgency */}
                          {applyUrgency.length > 0 && (
                            <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                              <div className="flex items-center gap-2 mb-3">
                                <Lightning className="w-5 h-5" style={{color:'var(--yellow)'}} />
                                <h3 className="font-extrabold text-sm">Urgent Applications</h3>
                              </div>
                              <div className="space-y-1.5">
                                {applyUrgency.map((item, i) => (
                                  <div key={i} className="flex items-start gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{item.title || item.company}</span>
                                    <span style={{color:'var(--text-dim)'}}>- {item.description || item.reason}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="space-y-4">
                          {/* Strengths */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <TrendUp className="w-5 h-5" style={{color:'var(--green)'}} />
                              <h3 className="font-extrabold text-sm">Your Strengths</h3>
                            </div>
                            {strengths.length > 0 ? (
                              <div className="space-y-1.5">
                                {strengths.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs">
                                    <span className="w-1.5 h-1.5 rounded-full" style={{background:'var(--green)'}} />
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.title || t.name}</span>
                                    <span style={{color:'var(--text-dim)'}}>- {t.description || t.detail}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No strong matches yet</div>
                            )}
                          </div>

                          {/* Weaknesses */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-5 h-5" style={{color:'var(--yellow)'}} />
                              <h3 className="font-extrabold text-sm">What to Learn</h3>
                            </div>
                            {weaknesses.length > 0 ? (
                              <div className="space-y-1.5">
                                {weaknesses.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs">
                                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.title || t.name}</span>
                                    <span style={{color:'var(--text-dim)'}}>- {t.description || t.detail}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No urgent learning needed</div>
                            )}
                          </div>

                          {/* Learning ROI (new) */}
                          {learningROI.length > 0 && (
                            <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                              <div className="flex items-center gap-2 mb-3">
                                <ChartLineUp className="w-5 h-5" style={{color:'var(--accent)'}} />
                                <h3 className="font-extrabold text-sm">Learning ROI</h3>
                              </div>
                              <div className="space-y-2">
                                {learningROI.slice(0, 6).map((item, i) => (
                                  <div key={i} className="p-2 rounded-lg hover:bg-[var(--surface2)] transition">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="font-semibold text-xs" style={{color:'var(--text)'}}>{item.skill}</span>
                                      <span className="text-[0.55rem] px-1.5 py-0.5 rounded font-bold" style={{background: item.impactScore >= 7 ? 'rgba(34,197,94,0.15)' : 'rgba(234,179,8,0.15)', color: item.impactScore >= 7 ? 'var(--green)' : 'var(--yellow)'}}>
                                        Impact: {item.impactScore}/10
                                      </span>
                                    </div>
                                    <div className="text-[0.6rem]" style={{color:'var(--text-dim)'}}>
                                      {item.jobsRequiring} jobs • {item.timeToLearn}
                                    </div>
                                    <div className="text-[0.6rem] mt-0.5" style={{color:'var(--text-dim)'}}>{item.reason}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* === SKILLS TAB === */}
                  {dashboardSubTab === 'skills' && (
                    <div className="space-y-5">
                      {/* Stats Row */}
                      <div className="grid grid-cols-5 gap-3">
                        {[
                          {n: techStackData.length || 0, l: 'Total Skills', c: 'var(--accent)', icon: <Wrench className="w-5 h-5" />},
                          {n: strongStack.length, l: 'Strong Match', c: 'var(--green)', icon: <TrendUp className="w-5 h-5" />},
                          {n: midStack.length, l: 'Moderate', c: 'var(--blue)', icon: <Stack className="w-5 h-5" />},
                          {n: weakStack.length, l: 'Gaps', c: 'var(--yellow)', icon: <BookOpen className="w-5 h-5" />},
                          {n: `${avgLevel}/5`, l: 'Avg Level', c: 'var(--purple)', icon: <ChartBar className="w-5 h-5" />},
                        ].map((s, i) => (
                          <div key={i} className="rounded-lg p-3 text-center border transition hover:border-[var(--accent)]" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="text-lg mb-0.5">{s.icon}</div>
                            <div className="text-xl font-extrabold" style={{color:s.c}}>{s.n}</div>
                            <div className="text-[0.6rem] uppercase tracking-wider" style={{color:'var(--text-dim)'}}>{s.l}</div>
                          </div>
                        ))}
                      </div>

                      <div className="grid grid-cols-[1fr_320px] gap-4">
                        <div className="space-y-4">
                          {/* Current Tech Stack */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Gear className="w-5 h-5" style={{color:'var(--accent)'}} />
                              <h3 className="font-extrabold text-sm">Current Tech Stack</h3>
                              <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)', color:'var(--text-dim)'}}>
                                {techStackData.length || 0} skills
                              </span>
                            </div>
                            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                              {techStackData.map((t, i) => <StackCard key={i} tech={t} />)}
                            </div>
                          </div>

                          {/* Technologies to Learn */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Brain className="w-5 h-5" style={{color:'var(--accent)'}} />
                              <h3 className="font-extrabold text-sm">Technologies to Master</h3>
                              <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(34,197,94,0.15)', color:'var(--green)'}}>
                                {techLearningData.length || 0} items
                              </span>
                            </div>
                            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                              {techLearningData.map((t, i) => <TechCard key={i} tech={t} />)}
                            </div>
                          </div>
                        </div>

                        <div className="space-y-4">
                          {/* Strengths from Stack */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <TrendUp className="w-5 h-5" style={{color:'var(--green)'}} />
                              <h3 className="font-extrabold text-sm">Your Strengths</h3>
                            </div>
                            {strongStack.length > 0 ? (
                              <div className="space-y-1.5">
                                {strongStack.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs">
                                    <span className="w-1.5 h-1.5 rounded-full" style={{background:'var(--green)'}} />
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                    <span style={{color:'var(--text-dim)'}}>- {t.roles}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No strong matches yet</div>
                            )}
                          </div>

                          {/* Learning Priorities */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <Target className="w-5 h-5" style={{color:'var(--green)'}} />
                              <h3 className="font-extrabold text-sm">Learning Priorities</h3>
                            </div>
                            {p1Tech.length > 0 || p2Tech.length > 0 ? (
                              <div className="space-y-2">
                                {p1Tech.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                    <span className="text-[0.55rem] px-1 py-0.5 rounded ml-auto" style={{background:'rgba(34,197,94,0.15)', color:'var(--green)'}}>P1</span>
                                  </div>
                                ))}
                                {p2Tech.map((t, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                    <span className="text-[0.55rem] px-1 py-0.5 rounded ml-auto" style={{background:'rgba(59,130,246,0.15)', color:'var(--blue)'}}>P2</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No urgent learning needed</div>
                            )}
                          </div>

                          {/* Skill Gaps */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-5 h-5" style={{color:'var(--yellow)'}} />
                              <h3 className="font-extrabold text-sm">Skill Gaps</h3>
                            </div>
                            {weakStack.length > 0 ? (
                              <div className="space-y-1.5">
                                {weakStack.map((t, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                    <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                    <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(234,179,8,0.15)', color:'var(--yellow)'}}>{t.ml}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs" style={{color:'var(--text-dim)'}}>No major gaps</div>
                            )}
                          </div>

                          {/* Level Distribution */}
                          <div className="rounded-lg border p-4" style={{background:'var(--surface)', borderColor:'var(--border)'}}>
                            <div className="flex items-center gap-2 mb-3">
                              <ChartBar className="w-5 h-5" style={{color:'var(--accent)'}} />
                              <h3 className="font-extrabold text-sm">Level Distribution</h3>
                            </div>
                            <div className="space-y-2">
                              {[
                                {label: 'Strong (5/5)', count: strongStack.length, color: 'var(--green)', bg: 'rgba(34,197,94,'},
                                {label: 'Good (4/5)', count: techStackData.filter(t => t.level === 4).length || 0, color: 'var(--blue)', bg: 'rgba(59,130,246,'},
                                {label: 'Moderate (3/5)', count: techStackData.filter(t => t.level === 3).length || 0, color: 'var(--yellow)', bg: 'rgba(234,179,8,'},
                                {label: 'Basic (2/5)', count: techStackData.filter(t => t.level === 2).length || 0, color: 'var(--orange)', bg: 'rgba(249,115,22,'},
                                {label: 'Beginner (1/5)', count: techStackData.filter(t => t.level === 1).length || 0, color: 'var(--red)', bg: 'rgba(239,68,68,'},
                              ].map((s, i) => (
                                <div key={i} className="flex items-center gap-2">
                                  <div className="w-20 text-[0.6rem]" style={{color:'var(--text-dim)'}}>{s.label}</div>
                                  <div className="flex-1 h-2 rounded-full" style={{background:'var(--surface2)'}}>
                                    <div className="h-full rounded-full" style={{
                                      width: `${techStackData.length ? (s.count / techStackData.length * 100) : 0}%`,
                                      background: `${s.bg}0.8)`
                                    }} />
                                  </div>
                                  <div className="w-6 text-right text-[0.6rem] font-bold" style={{color:s.color}}>{s.count}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}

            {/* === PREFERENCES === */}
            {tab === 'preferences' && (
              <PreferencesTab preferences={preferences} onUpdate={fetchPreferences} />
            )}
          </div>
        </div>
      </main>

      {/* Drawer */}
      {drawer && (() => {
        const drawerLocations = (() => {
          if (drawer.job.locations) {
            try {
              const locs = typeof drawer.job.locations === 'string' ? JSON.parse(drawer.job.locations) : drawer.job.locations
              return locs.length ? locs : [drawer.job.location]
            } catch { return [drawer.job.location] }
          }
          return [drawer.job.location]
        })()
        return (
        <>
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" onClick={() => setDrawer(null)} />
          <div className="fixed top-0 right-0 w-[min(640px,92vw)] h-full z-[101] overflow-y-auto p-4 border-l"
            style={{background:'var(--surface)',borderColor:'var(--border)'}}>
            <button onClick={() => setDrawer(null)} className="absolute top-3 right-3 w-7 h-7 rounded-md border flex items-center justify-center text-sm hover:bg-red-500 hover:border-red-500 hover:text-white transition"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>✕</button>
            <div className="flex gap-4 mb-3">
              {/* Left: Score, Company, Role, Locations */}
              <div className="flex-1 min-w-0">
                <div className={`text-4xl font-black mb-1 ${getScoreColor(drawer.job.score)}`}>{drawer.job.score}<span className="text-lg font-bold opacity-50">/100</span></div>
                <div className="text-lg font-extrabold truncate">{drawer.job.company}</div>
                <div className="text-sm mb-2 truncate" style={{color:'var(--text-dim)'}}>{drawer.job.role}</div>
                <div className="flex flex-wrap gap-1">
                  {drawerLocations.map((loc, i) => {
                    const lcc = CITY_COLORS[loc] || DEFAULT_CITY_COLOR
                    return <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:lcc.bg,color:lcc.text}}>📍 {loc}</span>
                  })}
                </div>
              </div>
              {/* Right: Match, Action, Work type, Visa */}
              <div className="flex flex-col items-end gap-1.5 shrink-0">
                <span className={`inline-flex px-2 py-0.5 rounded text-[0.6rem] font-semibold uppercase ${getMatchClass(drawer.job.match)}`}>{drawer.job.match}</span>
                {drawer.job.action && (
                  <div className="text-[0.6rem] font-semibold px-2 py-1 rounded-lg text-right max-w-[180px]" style={{background: drawer.job.score>=75?'rgba(34,197,94,0.12)':drawer.job.score>=50?'rgba(234,179,8,0.12)':'rgba(239,68,68,0.12)', color: drawer.job.score>=75?'var(--green)':drawer.job.score>=50?'var(--yellow)':'var(--red)'}}>
                    {drawer.job.action}
                  </div>
                )}
                {drawer.job.visa && drawer.job.visa !== 'Uncertain' && (() => {
                  const vs = VISA_STYLES[drawer.job.visa] || VISA_STYLES['Uncertain']
                  return <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold" style={{background:vs.bg,color:vs.text}}><IdentificationCard className="w-2.5 h-2.5" />{vs.label}</span>
                })()}
                {drawer.job.work_type && <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>{drawer.job.work_type}</span>}
              </div>
            </div>
            <div className="flex gap-2 mb-3">
              <a href={drawer.job.url} target="_blank" rel="noreferrer"
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-bold text-white transition hover:opacity-90"
                style={{background:'var(--accent)'}}>
                <Link className="w-4 h-4" /> Open Job Page
              </a>
              <button onClick={() => { navigator.clipboard.writeText(drawer.job.url); setToast('Copied!'); setTimeout(() => setToast(null), 2000) }}
                className="px-3 py-2 rounded-lg text-sm font-bold border transition hover:border-[var(--accent)]"
                style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>
                Copy URL
              </button>
            </div>
            <div className="flex gap-1 mb-3 border-b pb-2" style={{borderColor:'var(--border)'}}>
              {['details','structured','summary','resume'].map(t => (
                <button key={t} onClick={() => setDrawerTab(t)}
                  className={`px-3 py-1 text-sm font-semibold rounded transition capitalize`}
                  style={{color: drawerTab===t ? 'var(--accent)' : 'var(--text-dim)', background: drawerTab===t ? 'rgba(99,102,241,0.1)' : 'transparent'}}>{t}</button>
              ))}
            </div>
            {drawerTab === 'details' && (() => {
              let sd = null
              try { sd = drawer.job.structured_description ? JSON.parse(drawer.job.structured_description) : null } catch {}
              return (
              <div>
                <ul className="text-sm space-y-1 mb-3" style={{color:'var(--text-dim)'}}>
                  <li><b style={{color:'var(--text)'}}>Salary:</b> {drawer.job.salary}</li>
                  <li><b style={{color:'var(--text)'}}>Industry:</b> {drawer.job.industry}</li>
                  <li><b style={{color:'var(--text)'}}>Domain:</b> {drawer.job.domain}</li>
                  <li><b style={{color:'var(--text)'}}>Posted:</b> {drawer.job.posted}</li>
                  <li><b style={{color:'var(--text)'}}>Applicants:</b> {drawer.job.applicants}</li>
                  <li><b style={{color:'var(--text)'}}>Visa:</b> {drawer.job.visa}</li>
                  <li><b style={{color:'var(--text)'}}>Work Type:</b> {drawer.job.work_type}</li>
                  {sd?.company_size && <li><b style={{color:'var(--text)'}}>Company Size:</b> {sd.company_size}</li>}
                </ul>
                <Sec title="Stack"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.job.stack}</p></Sec>
                {sd?.company_description && (
                  <Sec title="About the Company"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.company_description}</p></Sec>
                )}
                {sd?.responsibilities?.length > 0 && (
                  <Sec title="Key Responsibilities">
                    <ul className="text-sm space-y-1">
                      {sd.responsibilities.map((r, i) => (
                        <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}>
                          <Lightning className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{color:'var(--accent)'}} />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </Sec>
                )}
                {sd?.requirements?.length > 0 && (
                  <Sec title="Requirements">
                    <ul className="text-sm space-y-1">
                      {sd.requirements.map((r, i) => (
                        <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}>
                          <ListChecks className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{color:'var(--green)'}} />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </Sec>
                )}
                {sd?.nice_to_have?.length > 0 && (
                  <Sec title="Nice to Have">
                    <ul className="text-sm space-y-1">
                      {sd.nice_to_have.map((r, i) => (
                        <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}>
                          <Star className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{color:'var(--yellow)'}} />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </Sec>
                )}
                {sd?.benefits?.length > 0 && (
                  <Sec title="Benefits">
                    <ul className="text-sm space-y-1">
                      {sd.benefits.map((r, i) => (
                        <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}>
                          <Gift className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{color:'var(--purple)'}} />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </Sec>
                )}
                {sd?.visa_reason && (
                  <Sec title="Visa Assessment">
                    <p className="text-sm flex items-start gap-2" style={{color:'var(--text-dim)'}}>
                      <Shield className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{color:'var(--accent)'}} />
                      <span>{sd.visa_reason}</span>
                    </p>
                  </Sec>
                )}
                <Sec title="Analysis"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.job.notes}</p></Sec>
              </div>
              )
            })()}
            {drawerTab === 'structured' && (() => {
              let sd = null
              try { sd = drawer.job.structured_description ? JSON.parse(drawer.job.structured_description) : null } catch {}
              if (!sd) return <div className="text-xs py-4 text-center" style={{color:'var(--text-dim)'}}>No structured data available</div>
              return (
              <div>
                {sd.company && <Sec title="Company"><p className="text-sm font-semibold" style={{color:'var(--text)'}}>{sd.company}</p></Sec>}
                {sd.role && <Sec title="Role"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.role}</p></Sec>}
                {sd.location && <Sec title="Location"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.location}{sd.locations?.length > 1 ? ` (+${sd.locations.length - 1} more)` : ''}</p></Sec>}
                {sd.employment_type && <Sec title="Employment"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.employment_type}</p></Sec>}
                {sd.work_types?.length > 0 && <Sec title="Work Types"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.work_types.join(', ')}</p></Sec>}
                {sd.salary && sd.salary !== 'Not specified' && <Sec title="Salary"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.salary}</p></Sec>}
                {sd.stack && <Sec title="Tech Stack"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.stack}</p></Sec>}
                {sd.visa && <Sec title="Visa"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.visa} {sd.visa_reason ? `— ${sd.visa_reason}` : ''}</p></Sec>}
                {sd.applicants && sd.applicants !== 'Not specified' && <Sec title="Applicants"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.applicants}</p></Sec>}
                {sd.industry && <Sec title="Industry"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.industry}</p></Sec>}
                {sd.domain && <Sec title="Domain"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.domain}</p></Sec>}
                {sd.company_size && <Sec title="Company Size"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.company_size}</p></Sec>}
                {sd.company_description && <Sec title="About"><p className="text-sm" style={{color:'var(--text-dim)'}}>{sd.company_description}</p></Sec>}
                {sd.requirements?.length > 0 && (
                  <Sec title="Requirements">
                    <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}><ListChecks className="w-3 h-3 shrink-0 mt-0.5" style={{color:'var(--green)'}} /><span>{r}</span></li>)}</ul>
                  </Sec>
                )}
                {sd.nice_to_have?.length > 0 && (
                  <Sec title="Nice to Have">
                    <ul className="text-sm space-y-1">{sd.nice_to_have.map((r, i) => <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}><Star className="w-3 h-3 shrink-0 mt-0.5" style={{color:'var(--yellow)'}} /><span>{r}</span></li>)}</ul>
                  </Sec>
                )}
                {sd.responsibilities?.length > 0 && (
                  <Sec title="Responsibilities">
                    <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}><Lightning className="w-3 h-3 shrink-0 mt-0.5" style={{color:'var(--accent)'}} /><span>{r}</span></li>)}</ul>
                  </Sec>
                )}
                {sd.benefits?.length > 0 && (
                  <Sec title="Benefits">
                    <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2" style={{color:'var(--text-dim)'}}><Gift className="w-3 h-3 shrink-0 mt-0.5" style={{color:'var(--purple)'}} /><span>{r}</span></li>)}</ul>
                  </Sec>
                )}
                {drawer.job.structured_file_path && <Sec title="File"><p className="text-[0.6rem] font-mono" style={{color:'var(--text-dim)'}}>{drawer.job.structured_file_path}</p></Sec>}
              </div>
              )
            })()}
            {drawerTab === 'summary' && drawer.summary && (
              <div>
                <Sec title="Summary"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.summary.summary}</p></Sec>
                <Sec title="Stack Required"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.summary.stack}</p></Sec>
                <Sec title="Resume Fit"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.summary.resumeFit}</p></Sec>
                <Sec title="Note"><p className="text-sm font-semibold" style={{color: drawer.summary.score>=75?'var(--green)':drawer.summary.score>=50?'var(--yellow)':'var(--red)'}}>{drawer.summary.note}</p></Sec>
              </div>
            )}
            {drawerTab === 'resume' && drawer.resume && (
              <div>
                <div className="flex gap-2 mb-3">
                  <button onClick={() => { const el = document.getElementById('resume-iframe'); if (el) { const doc = el.contentDocument || el.contentWindow.document; navigator.clipboard.writeText(doc.body.textContent) } }}
                    className="px-3 py-1 text-xs font-semibold rounded border transition hover:border-[var(--accent)]"
                    style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>Copy Resume</button>
                </div>
                <iframe id="resume-iframe" srcDoc={`<!DOCTYPE html><html><head><style>body{font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.6;color:#c9d1d9;margin:0;padding:16px;background:transparent;}a{color:#58a6ff;}h1,h2,h3{margin:0.5em 0;color:#e6edf3;}ul{padding-left:1.2em;}li{margin:0.25em 0;}</style></head><body>${drawer.resume.content}</body></html>`}
                  className="w-full border rounded-lg" style={{borderColor:'var(--border)',height:'500px',background:'transparent'}} />
              </div>
            )}
          </div>
        </>
        )
      })()}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[300] px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all duration-300" style={{background:'#22c55e'}}>
          {toast}
        </div>
      )}

      {/* Confirm Dialog */}
      {confirmDialog && (
        <>
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200]" onClick={() => { confirmDialog.resolve(false); setConfirmDialog(null) }} />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(400px,90vw)] z-[201] rounded-xl border p-5 shadow-2xl" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
            <h3 className="font-extrabold text-sm mb-2">{confirmDialog.title}</h3>
            <p className="text-xs mb-5" style={{color:'var(--text-dim)'}}>{confirmDialog.message}</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => { confirmDialog.resolve(false); setConfirmDialog(null) }}
                className="px-4 py-2 rounded-lg text-xs font-bold transition hover:opacity-80"
                style={{color:'var(--text-dim)'}}>
                Cancel
              </button>
              <button onClick={() => { confirmDialog.resolve(true); setConfirmDialog(null) }}
                className="px-4 py-2 rounded-lg text-xs font-bold text-white transition hover:opacity-90"
                style={{background: confirmDialog.variant === 'warning' ? '#eab308' : confirmDialog.variant === 'info' ? 'var(--accent)' : '#ef4444'}}>
                {confirmDialog.confirmLabel}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Duplicate Job Dialog */}
      {duplicateJob && (
        <>
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200]" onClick={() => setDuplicateJob(null)} />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(420px,90vw)] z-[201] rounded-xl border p-5 shadow-2xl" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
            <div className="flex items-center gap-2 mb-3">
              <Warning className="w-5 h-5" style={{color:'var(--yellow)'}} />
              <h3 className="font-extrabold text-sm">Job Already Exists</h3>
            </div>
            <div className="rounded-lg p-3 mb-4" style={{background:'var(--surface2)',border:'1px solid var(--border)'}}>
              <div className="text-sm font-bold">#{duplicateJob.num} {duplicateJob.company}</div>
              <div className="text-xs mt-1" style={{color:'var(--text-dim)'}}>
                Score: <span className="font-bold" style={{color: duplicateJob.score>=75?'var(--green)':duplicateJob.score>=50?'var(--yellow)':'var(--red)'}}>{duplicateJob.score}</span>
                {' · '}
                Match: <span className="font-bold" style={{color:'var(--accent)'}}>{duplicateJob.match}</span>
              </div>
            </div>
            <p className="text-xs mb-4" style={{color:'var(--text-dim)'}}>How would you like to update this job?</p>
            <div className="flex gap-2">
              <button onClick={async () => {
                  await fetch(`${API}/jobs/${duplicateJob.num}/rescore`, { method: 'POST' })
                  fetchPending(); refreshJobs()
                  setDuplicateJob(null)
                }}
                className="flex-1 px-3 py-2.5 rounded-lg text-xs font-bold transition hover:opacity-90"
                style={{background:'var(--accent)',color:'white'}}>
                <TrendUp className="w-3.5 h-3.5 inline mr-1" /> Rescore
              </button>
              <button onClick={async () => {
                  await fetch(`${API}/jobs/${duplicateJob.num}/requeue`, { method: 'POST' })
                  fetchPending(); refreshJobs()
                  setDuplicateJob(null)
                }}
                className="flex-1 px-3 py-2.5 rounded-lg text-xs font-bold transition hover:opacity-90"
                style={{background:'var(--surface2)',border:'1px solid var(--border)',color:'var(--text)'}}>
                <Repeat className="w-3.5 h-3.5 inline mr-1" /> Reprocess
              </button>
              <button onClick={() => setDuplicateJob(null)}
                className="px-3 py-2.5 rounded-lg text-xs font-bold transition hover:opacity-80"
                style={{color:'var(--text-dim)'}}>
                Cancel
              </button>
            </div>
          </div>
        </>
      )}

      {/* Workflow Terminal Drawer */}
      {workflowDrawer && (
        <>
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" onClick={() => { workflowWs.current?.close(); setWorkflowDrawer(null); setWorkflowLogs([]) }} />
          <div className="fixed top-0 right-0 w-[min(600px,92vw)] h-full z-[101] flex flex-col"
            style={{background:'var(--surface)',borderLeft:'1px solid var(--border)'}}>
            {/* Header */}
            <div className="px-4 py-2.5 flex items-center gap-2 border-b shrink-0" style={{borderColor:'var(--border)'}}>
              <span className="text-sm">💻</span>
              <span className="font-bold text-sm" style={{color:'var(--text)'}}>Workflow Terminal</span>
              <span className="text-[0.6rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>
                {workflowDrawer.company || 'Job'} #{workflowDrawer.job_num || '?'}
              </span>
              {workflowDrawer.status === 'processing' && (
                <span className="text-[0.55rem] px-1.5 py-0.5 rounded-full font-bold animate-pulse" style={{background:'rgba(99,102,241,0.2)',color:'var(--accent)',border:'1px solid rgba(99,102,241,0.3)'}}>
                  ● LIVE
                </span>
              )}
              <button onClick={() => { workflowWs.current?.close(); setWorkflowDrawer(null); setWorkflowLogs([]) }}
                className="ml-auto w-7 h-7 rounded-md border flex items-center justify-center text-sm transition hover:bg-red-500 hover:border-red-500 hover:text-white"
                style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>✕</button>
            </div>
            {/* Step progress bar */}
            <div className="px-4 py-2 flex gap-1 border-b shrink-0 overflow-x-auto" style={{borderColor:'var(--border)',background:'var(--surface2)'}}>
              {['fetch','validate','extract_raw','extract_struct','summary','resume','score','done'].map((s, i) => {
                const stepVal = workflowDrawer[`step_${s}`]
                const isDone = stepVal === 1
                const isActive = !isDone && workflowLogs.some(l => l.step === s)
                return (
                  <div key={s} className="flex items-center gap-0.5 shrink-0">
                    <div className="w-4 h-4 rounded-full flex items-center justify-center text-[0.45rem] font-bold transition-all"
                      style={{background: isDone ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--surface)',color: isDone || isActive ? 'white' : 'var(--text-dim)',border:`1px solid ${isDone ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--border)'}`}}>
                      {isDone ? <Check className="w-2.5 h-2.5" /> : isActive ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : i+1}
                    </div>
                    {i < 5 && <div className="h-[1px] w-3 rounded-full" style={{background: isDone ? '#22c55e' : 'var(--border)'}} />}
                  </div>
                )
              })}
            </div>
            {/* Terminal output */}
            <div ref={workflowEndRef} className="flex-1 overflow-y-auto p-3 font-mono text-[0.7rem] leading-relaxed" style={{background:'#0d1117',color:'#c9d1d9'}}>
              {workflowLogs.length === 0 && (
                <div className="text-center py-12" style={{color:'#484f58'}}>
                  <Spinner className="w-8 h-8 animate-spin" />
                  <div>Waiting for workflow output...</div>
                  <div className="text-[0.6rem] mt-1" style={{color:'#21262d'}}>WebSocket connecting to stream server...</div>
                </div>
              )}
              {workflowLogs.map((log, i) => {
                const stepColors = {start:'#8b949e',fetch:'#58a6ff',validate:'#22c55e',extract_raw:'#58a6ff',extract_struct:'#eab308',summary:'#f97316',resume:'#06b6d4',score:'#a371f7',done:'#3fb950',error:'#f85149',mimo:'#58a6ff',tool:'#a371f7',step:'#3fb950',cmd:'#58a6ff',out:'#c9d1d9',err:'#f85149',analyze:'#a371f7'}
                const isCmd = log.step === 'cmd'
                const isOut = log.step === 'out'
                const isErr = log.step === 'err'
                const isMimo = log.step === 'mimo'
                const isStep = log.step === 'step'
                const isError = log.step === 'error'
                const isDone = log.step === 'done'
                return (
                  <div key={i} className={`mb-0.5 ${isError || isErr ? 'bg-red-500/10 -mx-3 px-3 py-0.5 rounded' : ''}`}>
                    {isCmd ? (
                      <div className="flex gap-2">
                        <span style={{color:'#484f58'}} className="shrink-0">{log.ts}</span>
                        <span style={{color:'#58a6ff'}}>$</span>
                        <span style={{color:'#58a6ff'}}>{log.msg}</span>
                      </div>
                    ) : isOut ? (
                      <div className="pl-[70px]" style={{color:'#8b949e'}}>{log.msg}</div>
                    ) : isErr ? (
                      <div className="flex gap-2">
                        <span style={{color:'#484f58'}} className="shrink-0">{log.ts}</span>
                        <span style={{color:'#f85149'}}>✗</span>
                        <span style={{color:'#f85149'}}>{log.msg}</span>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <span style={{color:'#484f58'}} className="shrink-0">{log.ts}</span>
                        {!isMimo && !isStep && (
                          <span className="font-bold uppercase shrink-0" style={{color: stepColors[log.step] || '#c9d1d9', minWidth:'50px'}}>[{log.step}]</span>
                        )}
                        <span style={{color: isError ? '#f85149' : isDone ? '#3fb950' : isStep ? '#3fb950' : '#c9d1d9'}}
                          className={isMimo ? 'whitespace-pre-wrap' : ''}>
                          {isStep ? <><span style={{color:'#3fb950'}}>✓</span> {log.msg}</> :
                           isDone ? <><Confetti className="w-4 h-4 inline" style={{color:'#3fb950'}} /> {log.msg}</> :
                           log.msg}
                        </span>
                      </div>
                    )}
                  </div>
                )
              })}
              {workflowDrawer.status === 'processing' && (
                <div className="flex gap-2 mt-1">
                  <span style={{color:'#484f58'}}>{new Date().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}</span>
                  <span style={{color:'#22c55e'}}>$</span>
                  <span className="animate-pulse" style={{color:'#22c55e'}}>█</span>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

const STEPS = [
  {key:'step_fetch',icon:<Globe className="w-3 h-3" />,label:'Fetch'},
  {key:'step_validate',icon:<CheckCircle className="w-3 h-3" />,label:'Validate'},
  {key:'step_extract_raw',icon:<MagnifyingGlass className="w-3 h-3" />,label:'Raw'},
  {key:'step_extract_struct',icon:<MagnifyingGlass className="w-3 h-3" />,label:'Struct'},
  {key:'step_summary',icon:<Clipboard className="w-3 h-3" />,label:'Summary'},
  {key:'step_resume',icon:<FileText className="w-3 h-3" />,label:'Resume'},
  {key:'step_analyze',icon:<Brain className="w-3 h-3" />,label:'Score'},
  {key:'step_done',icon:<CheckCircle className="w-3 h-3" />,label:'Done'},
]

const STATUS_BADGE = {
  queued:     { bg:'linear-gradient(135deg, rgba(234,179,8,0.2), rgba(234,179,8,0.08))', border:'rgba(234,179,8,0.4)', fg:'#eab308', icon:<Clock className="w-3 h-3" />, pulse:false },
  processing: { bg:'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.15))', border:'rgba(99,102,241,0.3)', fg:'var(--accent)', icon:<Gear className="w-3 h-3" />, pulse:true },
  paused:     { bg:'linear-gradient(135deg, rgba(234,179,8,0.2), rgba(234,179,8,0.08))', border:'rgba(234,179,8,0.4)', fg:'#eab308', icon:<Pause className="w-3 h-3" />, pulse:false },
  fetching:   { bg:'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.08))', border:'rgba(59,130,246,0.4)', fg:'#3b82f6', icon:<Globe className="w-3 h-3" />, pulse:true },
  validating: { bg:'linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.08))', border:'rgba(34,197,94,0.4)', fg:'#22c55e', icon:<CheckCircle className="w-3 h-3" />, pulse:true },
  extractingraw:   { bg:'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.08))', border:'rgba(59,130,246,0.4)', fg:'#3b82f6', icon:<MagnifyingGlass className="w-3 h-3" />, pulse:true },
  extractingstruct: { bg:'linear-gradient(135deg, rgba(234,179,8,0.2), rgba(234,179,8,0.08))', border:'rgba(234,179,8,0.4)', fg:'#eab308', icon:<MagnifyingGlass className="w-3 h-3" />, pulse:true },
  analyzing:  { bg:'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(168,85,247,0.08))', border:'rgba(168,85,247,0.4)', fg:'#a855f7', icon:<Brain className="w-3 h-3" />, pulse:true },
  summarizing: { bg:'linear-gradient(135deg, rgba(249,115,22,0.2), rgba(249,115,22,0.08))', border:'rgba(249,115,22,0.4)', fg:'#f97316', icon:<Clipboard className="w-3 h-3" />, pulse:true },
  saving:     { bg:'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(6,182,212,0.08))', border:'rgba(6,182,212,0.4)', fg:'#06b6d4', icon:<FileText className="w-3 h-3" />, pulse:true },
  scoring:    { bg:'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(168,85,247,0.08))', border:'rgba(168,85,247,0.4)', fg:'#a855f7', icon:<Brain className="w-3 h-3" />, pulse:true },
  resuming:   { bg:'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(6,182,212,0.08))', border:'rgba(6,182,212,0.4)', fg:'#06b6d4', icon:<FileText className="w-3 h-3" />, pulse:true },
  done:       { bg:'linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.08))', border:'rgba(34,197,94,0.4)', fg:'#22c55e', icon:<CheckCircle className="w-3 h-3" />, pulse:false },
  failed:     { bg:'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.08))', border:'rgba(239,68,68,0.4)', fg:'#ef4444', icon:<X className="w-3 h-3" />, pulse:false },
}

function getProcessingStatus(item) {
  if (item.status === 'done') return 'done'
  if (item.status === 'failed') return 'failed'
  if (item.status === 'paused') return 'paused'
  if (item.status === 'processing') {
    const steps = [item.step_fetch, item.step_validate, item.step_extract_raw, item.step_extract_struct, item.step_summary, item.step_resume, item.step_analyze, item.step_done]
    const done = steps.filter(s => s === 1).length
    const labels = ['fetching','validating','extractingraw','extractingstruct','summarizing','saving','scoring','done']
    return labels[Math.min(done, labels.length - 1)] || 'processing'
  }
  return 'queued'
}

function PendingItem({ item, onDelete, onProcess, onReset, onPause, onDragStart, onViewWorkflow }) {
  const [processing, setProcessing] = useState(false)
  const statusKey = getProcessingStatus(item)
  const sc = STATUS_BADGE[statusKey] || STATUS_BADGE.processing
  const steps = [item.step_fetch, item.step_validate, item.step_extract_raw, item.step_extract_struct, item.step_summary, item.step_resume, item.step_analyze, item.step_done]
  const done = steps.filter(s => s === 1).length
  const isProcessing = statusKey !== 'queued' && statusKey !== 'done' && statusKey !== 'failed' && statusKey !== 'paused'
  const isPaused = statusKey === 'paused'
  const nextStep = isProcessing ? steps.findIndex(s => s !== 1) : -1

  const handleProcess = async () => {
    if (!onProcess || processing) return
    setProcessing(true)
    try {
      await onProcess()
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div draggable={!!onDragStart} onDragStart={onDragStart}
      className="rounded-lg border overflow-hidden transition-all duration-200 hover:shadow-lg" style={{background:'var(--surface)',borderColor:'var(--border)',cursor: onDragStart ? 'grab' : 'default'}}>
      {/* Header row */}
      <div className="px-3 pt-3 pb-2">
        {/* Row 1: badges + company + date */}
        <div className="flex items-center gap-1.5 flex-wrap mb-1.5">
          {/* Status badge */}
          <span className="inline-flex items-center gap-1 text-[0.6rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide shrink-0"
            style={{background:sc.bg,border:`1px solid ${sc.border}`,color:sc.fg,animation:sc.pulse?'pulse 2s ease-in-out infinite':'none'}}>
            <span style={{color:sc.fg}}>{sc.icon}</span>{item.status === 'done' ? 'Completed' : item.status === 'failed' ? 'Failed' : item.status === 'paused' ? 'Paused' : statusKey.charAt(0).toUpperCase() + statusKey.slice(1)}
          </span>
          {/* Source badge */}
          <span className="text-[0.55rem] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wider shrink-0"
            style={{background:item.source==='web'?'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.15))':'var(--surface2)',border:item.source==='web'?'1px solid rgba(99,102,241,0.3)':'1px solid var(--border)',color:item.source==='web'?'var(--accent)':'var(--text-dim)'}}>
            {item.source==='web'?'Web':'CLI'}
          </span>
          {item.company && <span className="text-xs font-bold truncate min-w-0" style={{color:'var(--text)'}}>{item.company}</span>}
          {item.job_num && <span className="text-[0.6rem] font-bold px-1 py-0.5 rounded shrink-0" style={{background:'var(--accent)',color:'white'}}>#{item.job_num}</span>}
          <span className="text-[0.6rem] ml-auto shrink-0" style={{color:'var(--text-dim)'}}>{new Date(item.created_at).toLocaleDateString()}</span>
        </div>
        {/* Row 2: action buttons */}
        <div className="flex items-center gap-1.5">
          {onProcess && statusKey === 'queued' && <button onClick={handleProcess} disabled={processing}
            className="h-6 px-2.5 rounded-full flex items-center gap-1 text-[0.6rem] font-bold transition disabled:opacity-60"
            style={{background:'linear-gradient(135deg, #10b981, #06b6d4)',color:'white',boxShadow:'0 0 8px rgba(16,185,129,0.3)'}}>
            <Rocket className="w-3 h-3" /> Process
          </button>}
          {isProcessing && (
            <>
              {onReset && <button onClick={onReset} title="Stop (restart from scratch)"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><X className="w-3 h-3" /></button>}
              {onPause && <button onClick={onPause} title="Pause (continue from current step)"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-yellow-500/20"
                style={{border:'1px solid rgba(234,179,8,0.4)',color:'#eab308'}}><Pause className="w-3 h-3" /></button>}
              {onProcess && <button onClick={handleProcess} title="Reprocess (restart from scratch)"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-green-500/20"
                style={{border:'1px solid rgba(34,197,94,0.4)',color:'#22c55e'}}><Repeat className="w-3 h-3" /></button>}
              {onDelete && <button onClick={onDelete} title="Remove"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><Trash className="w-3 h-3" /></button>}
            </>
          )}
          {isPaused && (
            <>
              {onProcess && <button onClick={handleProcess} disabled={processing}
                className="h-6 px-2.5 rounded-full flex items-center gap-1 text-[0.6rem] font-bold transition disabled:opacity-60"
                style={{background:'linear-gradient(135deg, #10b981, #06b6d4)',color:'white',boxShadow:'0 0 8px rgba(16,185,129,0.3)'}}>
                <Rocket className="w-3 h-3" /> Continue
              </button>}
              {onReset && <button onClick={onReset} title="Stop (restart from scratch)"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><X className="w-3 h-3" /></button>}
              {onDelete && <button onClick={onDelete} title="Remove"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><Trash className="w-3 h-3" /></button>}
            </>
          )}
          {statusKey === 'failed' && (
            <>
              {onReset && <button onClick={onReset} title="Stop (restart from scratch)"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><X className="w-3 h-3" /></button>}
              {onProcess && <button onClick={handleProcess} title="Retry processing"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-green-500/20"
                style={{border:'1px solid rgba(34,197,94,0.4)',color:'#22c55e'}}><Repeat className={`w-3 h-3 ${processing ? 'animate-spin' : ''}`} /></button>}
              {onDelete && <button onClick={onDelete} title="Remove"
                className="w-5 h-5 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}><Trash className="w-3 h-3" /></button>}
            </>
          )}
          {item.workflow_log && JSON.parse(item.workflow_log).length > 0 && (
            <button onClick={()=>onViewWorkflow && onViewWorkflow(item)} title="View workflow log"
              className="w-5 h-5 rounded flex items-center justify-center shrink-0 transition hover:bg-white/10 ml-auto"
              style={{border:'1px solid var(--border)',color:'var(--text-dim)'}}><FileText className="w-3 h-3" /></button>
          )}
        </div>
        {/* Title & Company */}
        {(item.title || item.company) && (
          <div className="px-1 mt-1.5 mb-1">
            {item.title && <div className="text-xs font-bold truncate" style={{color:'var(--text)'}}>{item.title}</div>}
            {item.company && item.company !== item.title && <div className="text-[0.6rem] truncate" style={{color:'var(--text-dim)'}}>{item.company}</div>}
          </div>
        )}
        {/* URL */}
        <div className="text-[0.55rem] truncate mb-2 px-1" style={{color:'var(--text-dim)',opacity:0.6}}>{item.url}</div>
      </div>

      {/* Steps pipeline */}
      <div className="px-3 pb-3">
        <div className="flex items-center gap-0 p-1.5 rounded-lg overflow-x-auto scrollbar-thin" style={{background:'var(--surface2)'}}>
          {STEPS.map((step, i) => {
            const d = steps[i] === 1
            const isActive = i === nextStep && !d && item.status !== 'done' && item.status !== 'failed'
            return (
              <div key={step.key} className="flex items-center shrink-0">
                <div className="flex flex-col items-center gap-px">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[0.5rem] transition-all duration-300"
                    style={{
                      background: d ? 'linear-gradient(135deg, #22c55e, #16a34a)' : isActive ? 'linear-gradient(135deg, var(--accent), var(--purple))' : 'var(--surface)',
                      color: d || isActive ? 'white' : 'var(--text-dim)',
                      boxShadow: d ? '0 0 6px rgba(34,197,94,0.4)' : isActive ? '0 0 6px rgba(99,102,241,0.4)' : 'none',
                      border: `1.5px solid ${d ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--border)'}`,
                      animation: isActive ? 'pulse 1.5s ease-in-out infinite' : 'none'
                    }}>
                    {d ? <Check className="w-2.5 h-2.5" /> : isActive ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : step.icon}
                  </div>
                  <span className="text-[0.4rem] font-semibold whitespace-nowrap" style={{color: d ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--text-dim)'}}>{step.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="h-[2px] w-2 mx-px rounded-full transition-all duration-300"
                    style={{background: d ? '#22c55e' : 'var(--border)'}} />
                )}
              </div>
            )
          })}
        </div>
        {/* Progress counter */}
        <div className="flex items-center justify-between mt-1.5">
          <div className="text-[0.6rem] font-semibold" style={{color:'var(--text-dim)'}}>
            {done}/{STEPS.length} steps
          </div>
          <div className="flex gap-0.5">
            {steps.map((s, i) => (
              <div key={i} className="w-1.5 h-1.5 rounded-full transition-all" style={{
                background: s === 1 ? '#22c55e' : i === nextStep && item.status !== 'done' && item.status !== 'failed' ? 'var(--accent)' : 'var(--border)'
              }} />
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {item.error && (
        <div className="mx-3 mb-3 px-3 py-2 rounded-lg text-[0.65rem]" style={{background:'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05))',border:'1px solid rgba(239,68,68,0.3)',color:'var(--red)'}}>
          <div className="flex items-start gap-2">
            <Warning className="w-4 h-4 shrink-0" />
            <div className="flex-1 min-w-0">
              {(() => {
                const err = item.error
                // Worker format: [source] Step 'xxx' failed: msg  OR  [source] msg
                let source = null, step = null, msg = err
                // Extract [source] prefix
                const srcMatch = err.match(/^\[(\w+)\]\s*/)
                if (srcMatch) {
                  source = srcMatch[1]
                  msg = err.slice(srcMatch[0].length)
                }
                // Extract Step 'xxx' failed: pattern
                const stepMatch = msg.match(/^Step\s+'(\w+)'\s+failed:\s*/)
                if (stepMatch) {
                  step = stepMatch[1]
                  msg = msg.slice(stepMatch[0].length)
                }
                // Source badge
                const sourceLabels = {fetch:'URL Fetch',mimo:'MiMo AI',db:'Database',worker:'Worker'}
                const sourceColors = {fetch:'#f97316',mimo:'var(--accent)',db:'#eab308',worker:'var(--red)'}
                return (
                  <>
                    <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                      {step && <span className="font-bold uppercase tracking-wide" style={{color:'var(--red)'}}>Step: {step}</span>}
                      {source && (
                        <span className="px-1.5 py-0.5 rounded text-[0.5rem] font-bold uppercase" style={{background:`${sourceColors[source]}20`,color:sourceColors[source],border:`1px solid ${sourceColors[source]}40`}}>
                          {sourceLabels[source] || source}
                        </span>
                      )}
                    </div>
                    <div className="break-all leading-relaxed" style={{color:'var(--text-dim)'}}>{msg.slice(0, 300)}</div>
                  </>
                )
              })()}
            </div>
          </div>
          <div className="mt-1.5 pt-1.5" style={{borderTop:'1px solid rgba(239,68,68,0.2)'}}>
            {onProcess && <span className="text-[0.55rem] font-semibold" style={{color:'var(--text-dim)'}}>Click Retry to restart</span>}
          </div>
        </div>
      )}
    </div>
  )
}

function CompactJobCard({ job, onClick }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const cc = CITY_COLORS[job.location] || DEFAULT_CITY_COLOR
  const vs = VISA_STYLES[job.visa] || VISA_STYLES['Uncertain']
  return (
    <div onClick={onClick} className="rounded-lg p-3 border cursor-pointer transition hover:shadow-lg hover:-translate-y-0.5" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftWidth:'3px',borderLeftColor:job.score>=75?'var(--green)':job.score>=50?'var(--yellow)':'var(--red)'}}>
      <div className="flex justify-between items-start mb-1">
        <div><div className="font-extrabold text-sm">{job.company}</div><div className="text-xs" style={{color:'var(--text-dim)'}}>{job.role}</div></div>
        <div className={`text-lg font-black ${getScoreColor(job.score)}`}>{job.score}</div>
      </div>
      <div className="flex flex-wrap gap-1 mb-2">
        {locations.slice(0, 3).map((loc, i) => {
          const lcc = CITY_COLORS[loc] || DEFAULT_CITY_COLOR
          return <span key={i} className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:lcc.bg,color:lcc.text}}>📍 {loc}</span>
        })}
        {locations.length > 3 && <span className="text-[0.55rem] px-1 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>+{locations.length - 3}</span>}
        <Tag>{job.work_type==='Remote'?<HouseSimple className="w-3 h-3 inline" />:job.work_type==='Hybrid'?<ArrowsClockwise className="w-3 h-3 inline" />:<Buildings className="w-3 h-3 inline" />} {job.work_type}</Tag>
        <Tag className={getMatchClass(job.match)}>{job.match}</Tag>
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:vs.bg,color:vs.text}}><IdentificationCard className="w-3 h-3" />{vs.label}</span>
        <Tag><Users className="w-3 h-3 inline" /> {job.applicants}</Tag>
      </div>
      <div className="text-xs pt-2 border-t" style={{color:'var(--text-dim)',borderColor:'var(--border)'}}><b style={{color:'var(--text)'}}>Stack:</b> {job.stack}</div>
    </div>
  )
}

function JobCard({ job, rank, onClick, onRescore, onDelete, onRequeue, onViewWorkflow }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const cc = CITY_COLORS[job.location] || DEFAULT_CITY_COLOR
  const vs = VISA_STYLES[job.visa] || VISA_STYLES['Uncertain']
  const hasLogs = job.workflow_log && JSON.parse(job.workflow_log).length > 0
  const isRescoring = job.rescoring === 1
  return (
    <div className="rounded-lg p-3 border transition hover:shadow-lg hover:-translate-y-0.5" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftWidth:'3px',borderLeftColor:job.score>=75?'var(--green)':job.score>=50?'var(--yellow)':'var(--red)'}}>
      <div className="flex justify-between items-center mb-1">
        <span onClick={onClick} className="cursor-pointer"><span className={`text-xs font-semibold ${rank<=3?'text-[var(--accent)]':''}`} style={{color:rank>3?'var(--text-dim)':undefined}}>#{rank}</span></span>
        <div className="flex items-center gap-1">
          {isRescoring && <span className="text-[0.5rem] font-bold px-1.5 py-0.5 rounded-full animate-pulse" style={{background:'rgba(99,102,241,0.15)',color:'var(--accent)',border:'1px solid rgba(99,102,241,0.25)'}}>Rescoring</span>}
          {hasLogs && onViewWorkflow && <button onClick={(e)=>{e.stopPropagation();onViewWorkflow({id:job.num,workflow_log:job.workflow_log,company:job.company,job_num:job.num})}} title="View workflow log" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}><FileText className="w-3 h-3" /></button>}
          {onRescore && <button onClick={async (e)=>{e.stopPropagation(); if(isRescoring){ const ok = await showConfirm('Rescore Running', 'Another rescore is already running. Start a new one?', 'Start New Rescore', 'warning'); if(!ok) return } onRescore(job.num)}} title="Rescore this job" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}><TrendUp className="w-3 h-3" /></button>}
          {onRequeue && <button onClick={(e)=>{e.stopPropagation();onRequeue(job.num)}} title="Reprocess from scratch (hard delete)" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-blue-500/20" style={{color:'var(--blue, #3b82f6)',border:'1px solid rgba(59,130,246,0.3)'}}><Repeat className="w-3 h-3" /></button>}
          {onDelete && <button onClick={(e)=>{e.stopPropagation();onDelete(job.num)}} title="Hide this job" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-red-500/20" style={{color:'var(--red)',border:'1px solid rgba(239,68,68,0.3)'}}><Trash className="w-3 h-3" /></button>}
          <span onClick={onClick} className={`cursor-pointer text-lg font-black ${getScoreColor(job.score)}`}>{job.score}</span>
        </div>
      </div>
      <div onClick={onClick} className="cursor-pointer">
        <div className="font-bold text-sm truncate">{job.company}</div>
        <div className="text-xs truncate mb-1.5" style={{color:'var(--text-dim)'}}>{job.role}</div>
      </div>
      <div className="flex gap-1 flex-wrap">
        {locations.slice(0, 2).map((loc, i) => {
          const lcc = CITY_COLORS[loc] || DEFAULT_CITY_COLOR
          return <span key={i} className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:lcc.bg,color:lcc.text}}>📍 {loc}</span>
        })}
        {locations.length > 2 && <span className="text-[0.55rem] px-1 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>+{locations.length - 2}</span>}
        <Tag>{job.work_type==='Remote'?<HouseSimple className="w-3 h-3 inline" />:job.work_type==='Hybrid'?<ArrowsClockwise className="w-3 h-3 inline" />:<Buildings className="w-3 h-3 inline" />} {job.work_type}</Tag>
        <Tag className={getMatchClass(job.match)}>{job.match}</Tag>
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:vs.bg,color:vs.text}}><IdentificationCard className="w-3 h-3" />{vs.label}</span>
        <Tag><Users className="w-3 h-3 inline" /> {job.applicants}</Tag>
      </div>
    </div>
  )
}

function TechCard({ tech }) {
  const pc = {p1:'bg-green-500/15 text-green-500',p2:'bg-blue-500/15 text-blue-500',p3:'bg-yellow-500/15 text-yellow-500',p4:'bg-orange-500/15 text-orange-500',p5:'bg-red-500/15 text-red-500'}
  return (
    <div className="rounded-lg p-3 border-l-3 transition hover:border-[var(--accent)]" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftColor:tech.pc==='p1'?'var(--green)':tech.pc==='p2'?'var(--blue)':tech.pc==='p3'?'var(--yellow)':tech.pc==='p4'?'var(--orange)':'var(--red)'}}>
      <div className="flex justify-between items-center mb-2"><span className="font-bold text-sm">{tech.name}</span><span className={`text-[0.6rem] font-bold px-2 py-0.5 rounded uppercase ${pc[tech.pc]}`}>{tech.pl}</span></div>
      <div className="flex items-center gap-2 text-xs mb-1.5" style={{color:'var(--text-dim)'}}><span>{tech.usage}%</span><div className="flex-1 h-[3px] rounded-full" style={{background:'var(--surface2)'}}><div className="h-full rounded-full" style={{width:`${tech.usage}%`,background:tech.uc}} /></div></div>
      <div className="text-xs mb-1.5" style={{color:'var(--text-dim)'}}><b style={{color:'var(--text)'}}>{tech.jobs}</b> — {tech.jd}</div>
      <div className="text-xs pt-1.5 border-t" style={{color:'var(--text-dim)',borderColor:'var(--border)'}} dangerouslySetInnerHTML={{__html:tech.reason}} />
      <div className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded text-[0.65rem]" style={{background:'var(--surface2)',color:'var(--text-dim)'}}><span className={`w-1 h-1 rounded-full ${tech.dc}`} /> {tech.sc} — {tech.action}</div>
    </div>
  )
}

function StackCard({ tech }) {
  return (
    <div className="rounded-lg p-3 border-l-3 transition hover:border-[var(--accent)]" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftColor:tech.mc==='p1'?'var(--green)':tech.mc==='p2'?'var(--blue)':tech.mc==='p3'?'var(--yellow)':'var(--red)'}}>
      <div className="flex justify-between items-center mb-2"><span className="font-bold text-sm">{tech.name}</span><span className="text-[0.6rem] font-bold px-2 py-0.5 rounded uppercase" style={{background:tech.mc==='p1'?'var(--green-dim)':tech.mc==='p2'?'rgba(59,130,246,0.15)':'var(--yellow-dim)',color:tech.mc==='p1'?'var(--green)':tech.mc==='p2'?'var(--blue)':'var(--yellow)'}}>{tech.ml}</span></div>
      <div className="flex gap-0.5 mb-2">{Array.from({length:5},(_,i)=><div key={i} className="flex-1 h-[3px] rounded-full" style={{background:i<tech.level?'var(--accent)':'var(--surface2)'}} />)}</div>
      <div className="text-xs mb-1" style={{color:'var(--text-dim)'}}><b style={{color:'var(--text)'}}>{tech.roles}</b></div>
      <div className="text-xs" style={{color:'var(--text-dim)'}}><b style={{color:'var(--accent)'}}>Path:</b> {tech.path}</div>
    </div>
  )
}

function PreferencesTab({ preferences, onUpdate }) {
  const [editing, setEditing] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [newPref, setNewPref] = useState({ category: 'scoring', key: '', value: '', description: '' })
  const [showAdd, setShowAdd] = useState(false)

  const categories = preferences ? Object.keys(preferences) : []
  const categoryIcons = { scoring: <ChartBar className="w-5 h-5" />, tech: <Wrench className="w-5 h-5" />, domain: <Buildings className="w-5 h-5" />, visa: <IdentificationCard className="w-5 h-5" />, strategy: <Target className="w-5 h-5" /> }

  const handleSave = async (id, value, description) => {
    await fetch(`${API}/preferences/${id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value, description })
    })
    setEditing(null)
    onUpdate()
  }

  const handleToggle = async (id, enabled) => {
    await fetch(`${API}/preferences/${id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enabled ? 1 : 0 })
    })
    onUpdate()
  }

  const handleDelete = async (id) => {
    await fetch(`${API}/preferences/${id}`, { method: 'DELETE' })
    onUpdate()
  }

  const handleAdd = async () => {
    if (!newPref.key || !newPref.value) return
    await fetch(`${API}/preferences`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preferences: [newPref] })
    })
    setNewPref({ category: 'scoring', key: '', value: '', description: '' })
    setShowAdd(false)
    onUpdate()
  }

  if (!preferences) return <div className="text-center py-12" style={{color:'var(--text-dim)'}}>Loading preferences...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-extrabold">Scoring Preferences</h2>
          <p className="text-sm" style={{color:'var(--text-dim)'}}>Configure how jobs are scored and analyzed. These preferences are used by the AI when processing jobs.</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)}
          className="px-3 py-1.5 rounded-lg text-xs font-bold transition"
          style={{background:'var(--accent)',color:'white'}}>
          {showAdd ? 'Cancel' : '+ Add Preference'}
        </button>
      </div>

      {/* Add new preference form */}
      {showAdd && (
        <div className="rounded-lg border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
          <h3 className="font-bold text-sm mb-3">Add New Preference</h3>
          <div className="grid grid-cols-4 gap-3">
            <select value={newPref.category} onChange={e => setNewPref({...newPref, category: e.target.value})}
              className="rounded-lg border px-3 py-2 text-sm" style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>
              <option value="scoring">Scoring</option>
              <option value="tech">Tech</option>
              <option value="domain">Domain</option>
              <option value="visa">Visa</option>
              <option value="strategy">Strategy</option>
            </select>
            <input value={newPref.key} onChange={e => setNewPref({...newPref, key: e.target.value})}
              placeholder="Key (e.g. relocation_package)" className="rounded-lg border px-3 py-2 text-sm"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}} />
            <input value={newPref.value} onChange={e => setNewPref({...newPref, value: e.target.value})}
              placeholder="Value (e.g. preferred)" className="rounded-lg border px-3 py-2 text-sm"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}} />
            <button onClick={handleAdd}
              className="rounded-lg px-3 py-2 text-sm font-bold transition"
              style={{background:'var(--green)',color:'white'}}>Save</button>
          </div>
          <input value={newPref.description} onChange={e => setNewPref({...newPref, description: e.target.value})}
            placeholder="Description (optional)" className="w-full rounded-lg border px-3 py-2 text-sm mt-2"
            style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}} />
        </div>
      )}

      {/* Preferences by category */}
      {categories.map(cat => (
        <div key={cat} className="rounded-lg border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
          <div className="flex items-center gap-2 mb-3">
            <span style={{color:'var(--accent)'}}>{categoryIcons[cat] || <Gear className="w-5 h-5" />}</span>
            <h3 className="font-extrabold text-sm capitalize">{cat}</h3>
            <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>
              {preferences[cat].length} items
            </span>
          </div>
          <div className="space-y-2">
            {preferences[cat].map(pref => (
              <div key={pref.id} className="flex items-center gap-3 p-2 rounded-lg transition hover:bg-[var(--surface2)]"
                style={{opacity: pref.enabled ? 1 : 0.5}}>
                <button onClick={() => handleToggle(pref.id, !pref.enabled)}
                  className="w-8 h-5 rounded-full transition relative"
                  style={{background: pref.enabled ? 'var(--green)' : 'var(--border)'}}>
                  <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition"
                    style={{left: pref.enabled ? '14px' : '2px'}} />
                </button>
                <div className="flex-1 min-w-0">
                  {editing === pref.id ? (
                    <div className="flex gap-2">
                      <input value={editValue} onChange={e => setEditValue(e.target.value)}
                        className="flex-1 rounded border px-2 py-1 text-xs"
                        style={{background:'var(--surface)',borderColor:'var(--accent)',color:'var(--text)'}} />
                      <input value={editDesc} onChange={e => setEditDesc(e.target.value)}
                        placeholder="Description" className="flex-1 rounded border px-2 py-1 text-xs"
                        style={{background:'var(--surface)',borderColor:'var(--border)',color:'var(--text)'}} />
                      <button onClick={() => handleSave(pref.id, editValue, editDesc)}
                        className="px-2 py-1 rounded text-[0.6rem] font-bold" style={{background:'var(--green)',color:'white'}}>Save</button>
                      <button onClick={() => setEditing(null)}
                        className="px-2 py-1 rounded text-[0.6rem]" style={{color:'var(--text-dim)'}}>Cancel</button>
                    </div>
                  ) : (
                    <>
                      <div className="text-xs font-semibold" style={{color:'var(--text)'}}>
                        <span className="font-mono" style={{color:'var(--accent)'}}>{pref.key}</span>
                        <span className="mx-1.5" style={{color:'var(--text-dim)'}}>=</span>
                        <span>{pref.value}</span>
                      </div>
                      {pref.description && <div className="text-[0.6rem] mt-0.5" style={{color:'var(--text-dim)'}}>{pref.description}</div>}
                    </>
                  )}
                </div>
                {editing !== pref.id && (
                  <div className="flex gap-1">
                    <button onClick={() => { setEditing(pref.id); setEditValue(pref.value); setEditDesc(pref.description || '') }}
                      className="w-6 h-6 rounded flex items-center justify-center text-[0.6rem] transition hover:bg-white/10"
                      style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}><PencilSimple className="w-3 h-3" /></button>
                    <button onClick={() => handleDelete(pref.id)}
                      className="w-6 h-6 rounded flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                      style={{color:'var(--red)',border:'1px solid rgba(239,68,68,0.3)'}}><Trash className="w-3 h-3" /></button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function Sec({ title, children }) { return <div className="mb-3"><h4 className="text-[0.6rem] uppercase tracking-wider mb-1" style={{color:'var(--accent)'}}>{title}</h4>{children}</div> }
function Tag({ children, className = '' }) { return <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] ${className}`} style={{background:className?undefined:'var(--surface2)',color:className?undefined:'var(--text-dim)'}}>{children}</span> }

export default App
