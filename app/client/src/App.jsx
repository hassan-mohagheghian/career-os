import { useState, useEffect, useMemo, useRef } from 'react'

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
  'BEST': { bg: 'rgba(34,197,94,0.2)', text: '#22c55e', label: '🛂 BEST' },
  'Strong': { bg: 'rgba(34,197,94,0.12)', text: '#4ade80', label: '🛂 Strong' },
  'Good': { bg: 'rgba(234,179,8,0.12)', text: '#facc15', label: '🛂 Good' },
  'Moderate': { bg: 'rgba(249,115,22,0.12)', text: '#fb923c', label: '🛂 Moderate' },
  'High': { bg: 'rgba(59,130,246,0.12)', text: '#60a5fa', label: '🛂 High' },
  'Uncertain': { bg: 'var(--surface2)', text: 'var(--text-dim)', label: '🛂 ?' },
  'N/A': { bg: 'var(--surface2)', text: 'var(--text-dim)', label: '🛂 N/A' },
}

function MultiSelect({ value, onChange, options, placeholder }) {
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
        className="px-1.5 py-0.5 rounded border text-[0.6rem] flex items-center gap-0.5 whitespace-nowrap transition"
        style={{background: hasValue ? 'rgba(99,102,241,0.15)' : 'var(--surface2)', borderColor: open ? 'var(--accent)' : hasValue ? 'var(--accent)' : 'var(--border)', color: hasValue ? 'var(--accent)' : 'var(--text-dim)'}}>
        {hasValue ? `${value.length} sel` : placeholder}
        <span className="text-[0.4rem]">▼</span>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-40 rounded-lg border shadow-lg max-h-40 overflow-y-auto"
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
  const [data, setData] = useState(null)
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

  const [sortBy, setSortBy] = useState('score')
  const [sortDir, setSortDir] = useState('desc')
  const [filterCities, setFilterCities] = useState([])
  const [filterCompanies, setFilterCompanies] = useState([])
  const [filterTech, setFilterTech] = useState('')
  const [filterMatches, setFilterMatches] = useState([])
  const [filterWorkTypes, setFilterWorkTypes] = useState([])
  const [filterEmploymentTypes, setFilterEmploymentTypes] = useState([])
  const [maximizedCol, setMaximizedCol] = useState(null) // null | 'queue' | 'processing' | 'failed' | 'done'
  const [dragOverCol, setDragOverCol] = useState(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const [preferences, setPreferences] = useState(null)

  useEffect(() => {
    fetch(`${API}/stream/all`).then(r => r.json()).then(setData)
    fetchPending()
    fetchPreferences()
  }, [])

  const fetchPreferences = () => fetch(`${API}/preferences`).then(r => r.json()).then(setPreferences)

  // SSE for real-time pending job updates + fallback polling
  useEffect(() => {
    let es
    const connect = () => {
      es = new EventSource(`${API}/pending/stream`)
      es.onmessage = (e) => { try { setPending(JSON.parse(e.data)) } catch {} }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    // Fallback: poll every 5s in case SSE drops
    const poll = setInterval(fetchPending, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [])

  // Sync tab with URL hash
  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace('#', '')
      if (h && h !== tab) setTab(h)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

  const fetchPending = () => fetch(`${API}/pending`).then(r => r.json()).then(setPending)

  const submitUrl = async () => {
    if (!urlInput.trim()) return
    setUrlError('')
    const rawUrl = urlInput.trim()

    // Client-side duplicate check (normalized URL)
    const normalizeUrl = (u) => {
      try {
        const url = new URL(u)
        return `${url.origin}${url.pathname}`.replace(/\/$/, '')
      } catch { return u.split('?')[0].replace(/\/$/, '') }
    }
    const baseUrl = normalizeUrl(rawUrl)
    const isDuplicate = pending.some(p => normalizeUrl(p.url) === baseUrl) ||
      (jobs && jobs.some(j => normalizeUrl(j.url) === baseUrl))
    if (isDuplicate) {
      setUrlError('This URL is already in the queue or processed.')
      return
    }

    setSubmitting(true)
    const res = await fetch(`${API}/pending`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: rawUrl, source: 'web' })
    })
    const data = await res.json()
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

  const rescoreJob = async (num) => {
    await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' }); fetchPending()
  }

  const rescoreAll = async () => {
    await fetch(`${API}/jobs/rescore-all`, { method: 'POST' }); fetchPending()
  }

  const deleteJob = async (num) => {
    if (!confirm(`Hide job #${num}? (Can be restored later)`)) return
    await fetch(`${API}/jobs/${num}`, { method: 'DELETE' })
    fetch(`${API}/stream/all`).then(r => r.json()).then(setData)
  }

  const requeueJob = async (num) => {
    if (!confirm(`Re-queue job #${num} for processing? Old version will be hidden.`)) return
    await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' })
    fetchPending()
    // Refresh data after a delay to allow processing
    setTimeout(() => fetch(`${API}/stream/all`).then(r => r.json()).then(setData), 5000)
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

  const { jobs, summaries, resumes, techLearning, techStack, cities, dashboardInsights } = data || {}

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

  const filteredJobs = useMemo(() => {
    if (!jobsWithLocations) return []
    let r = [...jobsWithLocations]
    if (filterCities.length) r = r.filter(j => j.parsedLocations.some(loc => filterCities.includes(loc)))
    if (filterCompanies.length) r = r.filter(j => filterCompanies.includes(j.company))
    if (filterTech) {
      const q = filterTech.toLowerCase()
      r = r.filter(j =>
        (j.stack && j.stack.toLowerCase().includes(q)) ||
        (j.role && j.role.toLowerCase().includes(q)) ||
        (j.company && j.company.toLowerCase().includes(q)) ||
        (j.notes && j.notes.toLowerCase().includes(q))
      )
    }
    if (filterMatches.length) r = r.filter(j => filterMatches.includes(j.match))
    if (filterWorkTypes.length) {
      r = r.filter(j => {
        // Check both work_type and work_types array
        let jWorkTypes = []
        if (j.work_types) {
          try {
            jWorkTypes = typeof j.work_types === 'string' ? JSON.parse(j.work_types) : j.work_types
          } catch { jWorkTypes = [] }
        }
        if (!jWorkTypes.length && j.work_type) jWorkTypes = [j.work_type]
        return filterWorkTypes.some(wt => jWorkTypes.includes(wt))
      })
    }
    if (filterEmploymentTypes.length) {
      r = r.filter(j => filterEmploymentTypes.includes(j.employment_type || 'Full-time'))
    }
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
  }, [jobsWithLocations, sortBy, sortDir, filterCities, filterCompanies, filterTech, filterMatches, filterWorkTypes, filterEmploymentTypes])

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

  const switchTab = (t) => {
    setTab(t)
    window.location.hash = t
  }

  const tabs = [
    { id: 'scoreboard', icon: '💼', label: 'Jobs', badge: jobs?.length, section: 'jobs' },
    { id: 'dashboard', icon: '📊', label: 'Dashboard', section: 'analysis' },
    { id: 'skills', icon: '🧠', label: 'Skills', section: 'analysis' },
    { id: 'preferences', icon: '⚙️', label: 'Preferences', section: 'settings' },
  ]

  const [refreshing, setRefreshing] = useState({})

  const refreshDashboard = async () => {
    setRefreshing(r => ({...r, dashboard: true}))
    await fetch(`${API}/refresh/dashboard`, { method: 'POST' })
    fetch(`${API}/stream/all`).then(r => r.json()).then(setData)
    setRefreshing(r => ({...r, dashboard: false}))
  }

  const refreshSkills = async () => {
    setRefreshing(r => ({...r, skills: true}))
    await fetch(`${API}/refresh/skills`, { method: 'POST' })
    fetch(`${API}/stream/all`).then(r => r.json()).then(setData)
    setRefreshing(r => ({...r, skills: false}))
  }

  if (!data) return <div className="flex items-center justify-center h-screen" style={{color:'var(--text-dim)'}}>Loading...</div>

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
            <span><b className="text-[var(--text)]">{jobs.length}</b> Jobs</span>
            <span><b className="text-green-500">{jobs.filter(j=>j.match==='High').length}</b> High</span>
            <span><b className="text-purple-500">{sorted[0]?.score}</b> Top</span>
            <span><b className="text-cyan-500">{resumes.filter(r=>r.id!=='original').length}</b> Resumes</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs" style={{color:'var(--text-dim)'}}>July 15, 2026</span>
            <button onClick={() => setTheme(t => t==='dark'?'light':'dark')}
              className="w-8 h-8 rounded-lg border flex items-center justify-center text-sm transition hover:border-[var(--accent)]"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>
              {theme==='dark' ? '☀️' : '🌙'}
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
                { id:'queue', icon:'⏳', label:'Queue', count:qCount, color:'#eab308', bg:'rgba(234,179,8,' },
                { id:'processing', icon:'⚙️', label:'Processing', count:pCount, color:'var(--accent)', bg:'rgba(99,102,241,' },
                { id:'failed', icon:'❌', label:'Process Failed', count:fCount, color:'var(--red)', bg:'rgba(239,68,68,' },
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
                          <span className="text-xl">{col.icon}</span>
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
                          <span className="text-sm">{col.icon}</span>
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
                                {urlError && <div className="text-[0.55rem] mb-1 px-0.5" style={{color:'var(--red)'}}>⚠️ {urlError}</div>}
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
                                onProcess={()=>processPending(p.id)} onReset={()=>resetPending(p.id)} onDelete={()=>deletePending(p.id)} onViewWorkflow={openWorkflow} />)}
                            {col.id === 'processing' && pCount === 0 && <div className="text-center py-6 text-[0.6rem]" style={{color:'var(--text-dim)'}}>Nothing processing</div>}

                            {col.id === 'failed' && pending.filter(p=>p.status==='failed').map(p =>
                              <PendingItem key={p.id} item={p} onDelete={()=>deletePending(p.id)} onProcess={()=>processPending(p.id)} onViewWorkflow={openWorkflow} />)}
                            {col.id === 'failed' && fCount === 0 && <div className="text-center py-6 text-[0.6rem]" style={{color:'var(--text-dim)'}}>No failures</div>}
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
                          <span className="text-xl">✅</span>
                          <span className="text-base font-black" style={{color:'#22c55e'}}>{filteredJobs.length}</span>
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
                          <span className="text-sm">✅</span>
                          <span className="font-bold text-xs" style={{color:'#22c55e'}}>Processed</span>
                          <span className="text-[0.5rem] font-bold px-1.5 py-0.5 rounded-full" style={{background:'rgba(34,197,94,0.15)',color:'#22c55e'}}>{filteredJobs.length}</span>
                          <button onClick={(e)=>{e.stopPropagation();rescoreAll()}} title="Rescore all jobs" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10 ml-auto" style={{color:'#22c55e'}}>🔃</button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-2">
                          <div className="flex flex-wrap items-center gap-1 mb-1">
                            <MultiSelect value={filterCities} onChange={setFilterCities} placeholder="🏙️ City" options={allCities.map(c=>({value:c,label:c}))} />
                            <MultiSelect value={filterCompanies} onChange={setFilterCompanies} placeholder="🏢 Co" options={allCompanies.map(c=>({value:c,label:c}))} />
                            <div className="relative">
                              <input value={filterTech} onChange={e=>setFilterTech(e.target.value)}
                                placeholder="🔍 Search..."
                                className="px-2 py-1 rounded border text-xs min-w-[100px] transition"
                                style={{background: filterTech ? 'rgba(99,102,241,0.15)' : 'var(--surface2)', borderColor: filterTech ? 'var(--accent)' : 'var(--border)', color: filterTech ? 'var(--accent)' : 'var(--text-dim)'}} />
                              {filterTech && <button onClick={()=>setFilterTech('')} className="absolute right-1 top-1/2 -translate-y-1/2 text-[0.5rem]" style={{color:'var(--text-dim)'}}>✕</button>}
                            </div>
                            <MultiSelect value={filterMatches} onChange={setFilterMatches} placeholder="📊 Match" options={[{value:'High',label:'High'},{value:'Medium',label:'Medium'},{value:'Low',label:'Low'}]} />
                            <MultiSelect value={filterWorkTypes} onChange={setFilterWorkTypes} placeholder="🏠 Work" options={[{value:'On-site',label:'On-site'},{value:'Remote',label:'Remote'},{value:'Hybrid',label:'Hybrid'}]} />
                            <MultiSelect value={filterEmploymentTypes} onChange={setFilterEmploymentTypes} placeholder="💼 Emp" options={[{value:'Full-time',label:'Full-time'},{value:'Part-time',label:'Part-time'},{value:'Contract',label:'Contract'},{value:'Internship',label:'Internship'},{value:'Temporary',label:'Temporary'}]} />
                            {activeFilterCount > 0 && <button onClick={clearFilters} className="px-1.5 py-0.5 rounded text-[0.55rem] font-semibold transition hover:bg-red-500/20" style={{color:'var(--red)'}}>Clear</button>}
                          </div>
                          <div className="flex items-center gap-1 mb-1.5">
                            <span className="text-[0.55rem] mr-1" style={{color:'var(--text-dim)'}}>Sort:</span>
                            {[{key:'score',l:'Score'},{key:'created_at',l:'Newest'},{key:'posted_at',l:'Posted'},{key:'applicants',l:'Apps'},{key:'company',l:'Co'},{key:'location',l:'City'}].map(s=>(
                              <button key={s.key} onClick={()=>toggleSort(s.key)} className="px-1.5 py-0.5 rounded text-[0.55rem] font-semibold transition" style={{background:sortBy===s.key?'var(--accent)':'var(--surface2)',color:sortBy===s.key?'white':'var(--text-dim)',border:`1px solid ${sortBy===s.key?'var(--accent)':'var(--border)'}`}}>
                                {s.l}{sortBy===s.key?(sortDir==='desc'?'↓':'↑'):''}
                              </button>
                            ))}
                          </div>
                          <div style={isMax ? gridStyle : {display:'grid',gridTemplateColumns:'repeat(2, minmax(0, 1fr))',gap:'0.5rem'}}>
                            {filteredJobs.map((j,i) => <ScoreCard key={j.num} job={j} rank={i+1} onClick={()=>openDrawer(j.num)} onRescore={rescoreJob} onDelete={deleteJob} onRequeue={requeueJob} onViewWorkflow={openWorkflow} />)}
                          </div>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )
            })()}

            {/* === DASHBOARD === */}
            {tab === 'dashboard' && (() => {
              const highMatchJobs = jobs.filter(j => j.match === 'High')
              const applyNow = jobs.filter(j => j.score >= 75)
              const remoteJobs = jobs.filter(j => j.work_type === 'Remote')
              const visaReady = jobs.filter(j => j.visa === 'BEST' || j.visa === 'Strong')

              // Dynamic insights from backend
              const strategy = dashboardInsights?.filter(i => i.type === 'strategy') || []
              const strengths = dashboardInsights?.filter(i => i.type === 'strengths') || []
              const weaknesses = dashboardInsights?.filter(i => i.type === 'weaknesses') || []
              const visaCompanies = dashboardInsights?.filter(i => i.type === 'visa_companies') || []
              const applyUrgency = dashboardInsights?.filter(i => i.type === 'apply_urgency') || []

              return (
                <div className="space-y-5">
                  {/* Header with refresh */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-extrabold">Dashboard</h2>
                      <p className="text-sm" style={{color:'var(--text-dim)'}}>Job search strategy and insights.</p>
                    </div>
                    <button onClick={refreshDashboard} disabled={refreshing.dashboard}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition disabled:opacity-50"
                      style={{background: refreshing.dashboard ? 'var(--surface2)' : 'var(--accent)', color: refreshing.dashboard ? 'var(--text-dim)' : 'white'}}>
                      <span className={refreshing.dashboard ? 'animate-spin' : ''}>🔄</span>
                      {refreshing.dashboard ? 'Updating...' : 'Refresh Insights'}
                    </button>
                  </div>

                  {/* Hero Stats */}
                  <div className="grid grid-cols-6 gap-3">
                    {[
                      {n:jobs.length,l:'Total Jobs',c:'var(--accent)',icon:'💼'},
                      {n:highMatchJobs.length,l:'High Match',c:'var(--green)',icon:'🎯'},
                      {n:applyNow.length,l:'Apply Now (75+)',c:'var(--yellow)',icon:'🚀'},
                      {n:remoteJobs.length,l:'Remote',c:'var(--cyan)',icon:'🏠'},
                      {n:visaReady.length,l:'Visa Ready',c:'var(--purple)',icon:'🛂'},
                      {n:resumes.filter(r=>r.id!=='original').length,l:'Resumes',c:'var(--accent)',icon:'📄'},
                    ].map((s,i)=>(
                      <div key={i} className="rounded-xl p-4 border transition hover:border-[var(--accent)]" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="text-lg mb-1">{s.icon}</div>
                        <div className="text-2xl font-extrabold" style={{color:s.c}}>{s.n}</div>
                        <div className="text-[0.65rem] uppercase tracking-wider mt-0.5" style={{color:'var(--text-dim)'}}>{s.l}</div>
                      </div>
                    ))}
                  </div>

                  {/* Two-column layout */}
                  <div className="grid grid-cols-[1fr_320px] gap-4">
                    {/* Left: Apply Now + Top Matches */}
                    <div className="space-y-4">
                      {/* Apply Now */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🚀</span>
                          <h3 className="font-extrabold text-sm">Apply Now — Score 75+</h3>
                          <span className="text-[0.6rem] px-2 py-0.5 rounded-full font-bold" style={{background:'rgba(34,197,94,0.15)',color:'var(--green)'}}>{applyNow.length} jobs</span>
                        </div>
                        {applyNow.length === 0 ? (
                          <div className="text-center py-6 text-xs" style={{color:'var(--text-dim)'}}>No jobs scored 75+ yet</div>
                        ) : (
                          <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                            {applyNow.slice(0, 6).map(j => <JobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                          </div>
                        )}
                      </div>

                      {/* Apply Urgency (dynamic) */}
                      {applyUrgency.length > 0 && (
                        <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-lg">⚡</span>
                            <h3 className="font-extrabold text-sm">Urgent Applications</h3>
                          </div>
                          <div className="space-y-1.5">
                            {applyUrgency.map((item,i) => (
                              <div key={i} className="flex items-start gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                <span className="font-semibold" style={{color:'var(--text)'}}>{item.title}</span>
                                <span style={{color:'var(--text-dim)'}}>- {item.description}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* High Match Jobs */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🎯</span>
                          <h3 className="font-extrabold text-sm">High Match Jobs</h3>
                          <span className="text-[0.6rem] px-2 py-0.5 rounded-full font-bold" style={{background:'rgba(34,197,94,0.15)',color:'var(--green)'}}>{highMatchJobs.length} jobs</span>
                        </div>
                        {highMatchJobs.length === 0 ? (
                          <div className="text-center py-6 text-xs" style={{color:'var(--text-dim)'}}>No high match jobs</div>
                        ) : (
                          <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
                            {highMatchJobs.slice(0, 6).map(j => <JobCard key={j.num} job={j} onClick={() => openDrawer(j.num)} />)}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right sidebar: Strategy + Cities + Tech */}
                    <div className="space-y-4">
                      {/* Strategy Guide (dynamic) */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">📋</span>
                          <h3 className="font-extrabold text-sm">Strategy</h3>
                          {strategy.length === 0 && <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>Processing...</span>}
                        </div>
                        <div className="space-y-2">
                          {strategy.map((g,i)=>(
                            <div key={i} className="flex items-start gap-2 p-2 rounded-lg transition hover:bg-[var(--surface2)]" style={{borderLeft:'2px solid var(--accent)'}}>
                              <span className="text-sm shrink-0">{g.icon}</span>
                              <div><div className="font-bold text-xs">{g.title}</div><div className="text-[0.6rem]" style={{color:'var(--text-dim)'}}>{g.description}</div></div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Cities */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🌍</span>
                          <h3 className="font-extrabold text-sm">Cities</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          {cities?.map((c,i) => (
                            <div key={i} className="rounded-lg p-2 text-center border transition hover:border-[var(--accent)]" style={{background:'var(--surface2)',borderColor:'var(--border)'}}>
                              <div className="text-sm mb-0.5">{c.icon}</div>
                              <div className="font-bold text-xs">{c.name}</div>
                              <div className="text-[0.55rem]" style={{color:'var(--text-dim)'}}>{c.info}</div>
                              <div className="text-[0.55rem] font-semibold" style={{color:'var(--accent)'}}>{c.jobs}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Tech Strengths (dynamic) */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">💪</span>
                          <h3 className="font-extrabold text-sm">Your Strengths</h3>
                        </div>
                        {strengths.length > 0 ? (
                          <div className="space-y-1.5">
                            {strengths.map((t,i) => (
                              <div key={i} className="flex items-center gap-2 text-xs">
                                <span className="w-1.5 h-1.5 rounded-full" style={{background:'var(--green)'}} />
                                <span className="font-semibold" style={{color:'var(--text)'}}>{t.title}</span>
                                <span style={{color:'var(--text-dim)'}}>- {t.description}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs" style={{color:'var(--text-dim)'}}>No strong matches yet</div>
                        )}
                      </div>

                      {/* Tech Weaknesses (dynamic) */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">📚</span>
                          <h3 className="font-extrabold text-sm">What to Learn</h3>
                        </div>
                        {weaknesses.length > 0 ? (
                          <div className="space-y-1.5">
                            {weaknesses.map((t,i) => (
                              <div key={i} className="flex items-center gap-2 text-xs">
                                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                                <span className="font-semibold" style={{color:'var(--text)'}}>{t.title}</span>
                                <span style={{color:'var(--text-dim)'}}>- {t.description}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs" style={{color:'var(--text-dim)'}}>No urgent learning needed</div>
                        )}
                      </div>

                      {/* Visa Companies (dynamic) */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🛂</span>
                          <h3 className="font-extrabold text-sm">Visa Sponsorship</h3>
                        </div>
                        {visaCompanies.length > 0 ? (
                          <div className="space-y-1.5">
                            {visaCompanies.map((j,i) => (
                              <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                <span className="font-semibold" style={{color:'var(--text)'}}>{j.title}</span>
                                <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(34,197,94,0.15)',color:'var(--green)'}}>{j.description}</span>
                              </div>
                            ))}
                          </div>
                        ) : visaReady.length > 0 ? (
                          <div className="space-y-1.5">
                            {visaReady.map((j,i) => (
                              <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition cursor-pointer" onClick={() => openDrawer(j.num)}>
                                <span className="font-semibold" style={{color:'var(--text)'}}>{j.company}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[0.55rem] font-bold ${j.visa==='BEST'?'bg-green-500/15 text-green-500':'bg-green-500/10 text-green-400'}`}>{j.visa}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs" style={{color:'var(--text-dim)'}}>No visa-ready jobs</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}

            {/* === SKILLS (merged Tech Learn + Tech Stack) === */}
            {tab === 'skills' && (() => {
              const strongStack = techStack?.filter(t => t.mc === 'p1') || []
              const midStack = techStack?.filter(t => t.mc === 'p2') || []
              const weakStack = techStack?.filter(t => t.mc === 'p3' || t.mc === 'p4') || []
              const p1Tech = techLearning?.filter(t => t.pc === 'p1') || []
              const p2Tech = techLearning?.filter(t => t.pc === 'p2') || []
              const totalUsage = techStack?.reduce((sum, t) => sum + (t.level || 0), 0) || 0
              const avgLevel = techStack?.length ? (totalUsage / techStack.length).toFixed(1) : 0

              return (
                <div className="space-y-5">
                  {/* Header with refresh */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-extrabold">Skills & Technology</h2>
                      <p className="text-sm" style={{color:'var(--text-dim)'}}>
                        Your tech stack coverage, learning priorities, and market demand analysis.
                      </p>
                    </div>
                    <button onClick={refreshSkills} disabled={refreshing.skills}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition disabled:opacity-50"
                      style={{background: refreshing.skills ? 'var(--surface2)' : 'var(--accent)', color: refreshing.skills ? 'var(--text-dim)' : 'white'}}>
                      <span className={refreshing.skills ? 'animate-spin' : ''}>🔄</span>
                      {refreshing.skills ? 'Updating...' : 'Refresh Skills'}
                    </button>
                  </div>

                  {/* Stats Row */}
                  <div className="grid grid-cols-5 gap-3">
                    {[
                      {n: techStack?.length || 0, l: 'Total Skills', c: 'var(--accent)', icon: '🔧'},
                      {n: strongStack.length, l: 'Strong Match', c: 'var(--green)', icon: '💪'},
                      {n: midStack.length, l: 'Moderate', c: 'var(--blue)', icon: '📘'},
                      {n: weakStack.length, l: 'Gaps', c: 'var(--yellow)', icon: '📚'},
                      {n: `${avgLevel}/5`, l: 'Avg Level', c: 'var(--purple)', icon: '📊'},
                    ].map((s,i) => (
                      <div key={i} className="rounded-xl p-3 text-center border transition hover:border-[var(--accent)]" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="text-lg mb-0.5">{s.icon}</div>
                        <div className="text-xl font-extrabold" style={{color:s.c}}>{s.n}</div>
                        <div className="text-[0.6rem] uppercase tracking-wider" style={{color:'var(--text-dim)'}}>{s.l}</div>
                      </div>
                    ))}
                  </div>

                  {/* Two-column layout */}
                  <div className="grid grid-cols-[1fr_320px] gap-4">
                    {/* Left: Main content */}
                    <div className="space-y-4">
                      {/* Current Tech Stack */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">⚙️</span>
                          <h3 className="font-extrabold text-sm">Current Tech Stack</h3>
                          <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'var(--surface2)',color:'var(--text-dim)'}}>
                            {techStack?.length || 0} skills
                          </span>
                        </div>
                        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                          {techStack?.map((t,i) => <StackCard key={i} tech={t} />)}
                        </div>
                      </div>

                      {/* Technologies to Learn */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🧠</span>
                          <h3 className="font-extrabold text-sm">Technologies to Master</h3>
                          <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(34,197,94,0.15)',color:'var(--green)'}}>
                            {techLearning?.length || 0} items
                          </span>
                        </div>
                        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
                          {techLearning?.map((t,i) => <TechCard key={i} tech={t} />)}
                        </div>
                      </div>
                    </div>

                    {/* Right sidebar: Summary + Insights */}
                    <div className="space-y-4">
                      {/* Strengths from Preferences */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">💪</span>
                          <h3 className="font-extrabold text-sm">Your Strengths</h3>
                        </div>
                        {strongStack.length > 0 ? (
                          <div className="space-y-1.5">
                            {strongStack.map((t,i) => (
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
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">🎯</span>
                          <h3 className="font-extrabold text-sm">Learning Priorities</h3>
                        </div>
                        {p1Tech.length > 0 || p2Tech.length > 0 ? (
                          <div className="space-y-2">
                            {p1Tech.map((t,i) => (
                              <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                <span className="text-[0.55rem] px-1 py-0.5 rounded ml-auto" style={{background:'rgba(34,197,94,0.15)',color:'var(--green)'}}>P1</span>
                              </div>
                            ))}
                            {p2Tech.map((t,i) => (
                              <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                <span className="text-[0.55rem] px-1 py-0.5 rounded ml-auto" style={{background:'rgba(59,130,246,0.15)',color:'var(--blue)'}}>P2</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs" style={{color:'var(--text-dim)'}}>No urgent learning needed</div>
                        )}
                      </div>

                      {/* Skill Gaps */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">📚</span>
                          <h3 className="font-extrabold text-sm">Skill Gaps</h3>
                        </div>
                        {weakStack.length > 0 ? (
                          <div className="space-y-1.5">
                            {weakStack.map((t,i) => (
                              <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-[var(--surface2)] transition">
                                <span className="font-semibold" style={{color:'var(--text)'}}>{t.name}</span>
                                <span className="text-[0.55rem] px-1.5 py-0.5 rounded" style={{background:'rgba(234,179,8,0.15)',color:'var(--yellow)'}}>{t.ml}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs" style={{color:'var(--text-dim)'}}>No major gaps</div>
                        )}
                      </div>

                      {/* Skill Level Distribution */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">📊</span>
                          <h3 className="font-extrabold text-sm">Level Distribution</h3>
                        </div>
                        <div className="space-y-2">
                          {[
                            {label: 'Strong (5/5)', count: strongStack.length, color: 'var(--green)', bg: 'rgba(34,197,94,'},
                            {label: 'Good (4/5)', count: techStack?.filter(t => t.level === 4).length || 0, color: 'var(--blue)', bg: 'rgba(59,130,246,'},
                            {label: 'Moderate (3/5)', count: techStack?.filter(t => t.level === 3).length || 0, color: 'var(--yellow)', bg: 'rgba(234,179,8,'},
                            {label: 'Basic (2/5)', count: techStack?.filter(t => t.level === 2).length || 0, color: 'var(--orange)', bg: 'rgba(249,115,22,'},
                            {label: 'Beginner (1/5)', count: techStack?.filter(t => t.level === 1).length || 0, color: 'var(--red)', bg: 'rgba(239,68,68,'},
                          ].map((s,i) => (
                            <div key={i} className="flex items-center gap-2">
                              <div className="w-20 text-[0.6rem]" style={{color:'var(--text-dim)'}}>{s.label}</div>
                              <div className="flex-1 h-2 rounded-full" style={{background:'var(--surface2)'}}>
                                <div className="h-full rounded-full" style={{
                                  width: `${techStack?.length ? (s.count / techStack.length * 100) : 0}%`,
                                  background: `${s.bg}0.8)`
                                }} />
                              </div>
                              <div className="w-6 text-right text-[0.6rem] font-bold" style={{color:s.color}}>{s.count}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Quick Actions */}
                      <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-lg">⚡</span>
                          <h3 className="font-extrabold text-sm">Quick Actions</h3>
                        </div>
                        <div className="space-y-2">
                          <button onClick={() => switchTab('preferences')}
                            className="w-full text-left text-xs p-2 rounded-lg hover:bg-[var(--surface2)] transition flex items-center gap-2"
                            style={{color:'var(--text)'}}>
                            <span>⚙️</span> Edit scoring preferences
                          </button>
                          <button onClick={() => switchTab('dashboard')}
                            className="w-full text-left text-xs p-2 rounded-lg hover:bg-[var(--surface2)] transition flex items-center gap-2"
                            style={{color:'var(--text)'}}>
                            <span>📊</span> View dashboard insights
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
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
          <div className="fixed top-0 right-0 w-[min(500px,92vw)] h-full z-[101] overflow-y-auto p-4 border-l"
            style={{background:'var(--surface)',borderColor:'var(--border)'}}>
            <button onClick={() => setDrawer(null)} className="absolute top-3 right-3 w-7 h-7 rounded-md border flex items-center justify-center text-sm hover:bg-red-500 hover:border-red-500 hover:text-white transition"
              style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>✕</button>
            <span className={`inline-flex px-2 py-0.5 rounded text-[0.6rem] font-semibold uppercase mb-1 ${getMatchClass(drawer.job.match)}`}>{drawer.job.match} Match</span>
            <div className={`text-4xl font-black mb-1 ${getScoreColor(drawer.job.score)}`}>{drawer.job.score}/100</div>
            <div className="text-lg font-extrabold">{drawer.job.company}</div>
            <div className="text-sm mb-3" style={{color:'var(--text-dim)'}}>{drawer.job.role}</div>
            <div className="flex flex-wrap gap-1 mb-3">
              {drawerLocations.map((loc, i) => {
                const lcc = CITY_COLORS[loc] || DEFAULT_CITY_COLOR
                return <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:lcc.bg,color:lcc.text}}>📍 {loc}</span>
              })}
            </div>
            <div className="flex gap-1 mb-3 border-b pb-2" style={{borderColor:'var(--border)'}}>
              {['details','summary','resume'].map(t => (
                <button key={t} onClick={() => setDrawerTab(t)}
                  className={`px-3 py-1 text-sm font-semibold rounded transition capitalize`}
                  style={{color: drawerTab===t ? 'var(--accent)' : 'var(--text-dim)', background: drawerTab===t ? 'rgba(99,102,241,0.1)' : 'transparent'}}>{t}</button>
              ))}
            </div>
            {drawerTab === 'details' && (
              <div>
                <ul className="text-sm space-y-1 mb-3" style={{color:'var(--text-dim)'}}>
                  <li><b style={{color:'var(--text)'}}>Salary:</b> {drawer.job.salary}</li>
                  <li><b style={{color:'var(--text)'}}>Industry:</b> {drawer.job.industry}</li>
                  <li><b style={{color:'var(--text)'}}>Domain:</b> {drawer.job.domain}</li>
                  <li><b style={{color:'var(--text)'}}>Posted:</b> {drawer.job.posted}</li>
                  <li><b style={{color:'var(--text)'}}>Applicants:</b> {drawer.job.applicants}</li>
                  <li><b style={{color:'var(--text)'}}>Visa:</b> {drawer.job.visa}</li>
                  <li><b style={{color:'var(--text)'}}>Work Type:</b> {drawer.job.work_type}</li>
                </ul>
                <Sec title="Stack"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.job.stack}</p></Sec>
                <Sec title="Analysis"><p className="text-sm" style={{color:'var(--text-dim)'}}>{drawer.job.notes}</p></Sec>
                <Sec title="Action"><p className="text-sm font-semibold" style={{color: drawer.job.score>=75?'var(--green)':drawer.job.score>=50?'var(--yellow)':'var(--red)'}}>{drawer.job.action}</p></Sec>
                <a href={drawer.job.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 px-3 py-2 rounded-md text-sm font-semibold text-white mt-2 transition hover:opacity-90" style={{background:'var(--accent)'}}>View on LinkedIn →</a>
              </div>
            )}
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
                  <button onClick={() => { const el = document.getElementById('resume-content'); if (el) navigator.clipboard.writeText(el.textContent) }}
                    className="px-3 py-1 text-xs font-semibold rounded border transition hover:border-[var(--accent)]"
                    style={{background:'var(--surface2)',borderColor:'var(--border)',color:'var(--text)'}}>Copy Resume</button>
                </div>
                <div id="resume-content" className="text-sm leading-relaxed" style={{color:'var(--text-dim)'}} dangerouslySetInnerHTML={{__html: drawer.resume.content}} />
              </div>
            )}
          </div>
        </>
        )
      })()}

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
            <div className="px-4 py-2 flex gap-1 border-b shrink-0" style={{borderColor:'var(--border)',background:'var(--surface2)'}}>
              {['fetch','analyze','resume','save','done'].map((s, i) => {
                const stepVal = workflowDrawer[`step_${s === 'done' ? 'done' : s}`] || workflowDrawer[s === 'done' ? 'step_done' : `step_${s}`]
                const isDone = stepVal === 1
                const isActive = !isDone && workflowLogs.some(l => l.step === s)
                return (
                  <div key={s} className="flex items-center gap-1 flex-1">
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-[0.5rem] font-bold transition-all"
                      style={{background: isDone ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--surface)',color: isDone || isActive ? 'white' : 'var(--text-dim)',border:`1px solid ${isDone ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--border)'}`}}>
                      {isDone ? '✓' : isActive ? <span className="animate-spin">⏳</span> : i+1}
                    </div>
                    {i < 4 && <div className="h-[2px] flex-1 rounded-full" style={{background: isDone ? '#22c55e' : 'var(--border)'}} />}
                  </div>
                )
              })}
            </div>
            {/* Terminal output */}
            <div ref={workflowEndRef} className="flex-1 overflow-y-auto p-3 font-mono text-[0.7rem] leading-relaxed" style={{background:'#0d1117',color:'#c9d1d9'}}>
              {workflowLogs.length === 0 && (
                <div className="text-center py-12" style={{color:'#484f58'}}>
                  <div className="text-2xl mb-2">⏳</div>
                  <div>Waiting for workflow output...</div>
                  <div className="text-[0.6rem] mt-1" style={{color:'#21262d'}}>WebSocket connecting to stream server...</div>
                </div>
              )}
              {workflowLogs.map((log, i) => {
                const stepColors = {start:'#8b949e',fetch:'#58a6ff',analyze:'#a371f7',resume:'#3fb950',save:'#d29922',done:'#3fb950',error:'#f85149',mimo:'#58a6ff',tool:'#a371f7',step:'#3fb950',raw:'#8b949e',cmd:'#58a6ff',out:'#c9d1d9',err:'#f85149'}
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
                           isDone ? <><span style={{color:'#3fb950'}}>🎉</span> {log.msg}</> :
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

const STEPS = [{key:'step_fetch',icon:'🌐',label:'Fetch'},{key:'step_analyze',icon:'🔍',label:'Analyze'},{key:'step_resume',icon:'📄',label:'Resume'},{key:'step_db',icon:'💾',label:'Save'},{key:'step_done',icon:'✅',label:'Done'}]

const STATUS_BADGE = {
  queued:     { bg:'linear-gradient(135deg, rgba(234,179,8,0.2), rgba(234,179,8,0.08))', border:'rgba(234,179,8,0.4)', fg:'#eab308', icon:'⏳', pulse:false },
  processing: { bg:'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.15))', border:'rgba(99,102,241,0.3)', fg:'var(--accent)', icon:'⚙️', pulse:true },
  fetching:   { bg:'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.08))', border:'rgba(59,130,246,0.4)', fg:'#3b82f6', icon:'🌐', pulse:true },
  analyzing:  { bg:'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(168,85,247,0.08))', border:'rgba(168,85,247,0.4)', fg:'#a855f7', icon:'🔍', pulse:true },
  resumed:    { bg:'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(6,182,212,0.08))', border:'rgba(6,182,212,0.4)', fg:'#06b6d4', icon:'📄', pulse:true },
  saving:     { bg:'linear-gradient(135deg, rgba(249,115,22,0.2), rgba(249,115,22,0.08))', border:'rgba(249,115,22,0.4)', fg:'#f97316', icon:'💾', pulse:true },
  done:       { bg:'linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.08))', border:'rgba(34,197,94,0.4)', fg:'#22c55e', icon:'✅', pulse:false },
  failed:     { bg:'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.08))', border:'rgba(239,68,68,0.4)', fg:'#ef4444', icon:'❌', pulse:false },
}

function getProcessingStatus(item) {
  if (item.status === 'done') return 'done'
  if (item.status === 'failed') return 'failed'
  if (item.status === 'processing') {
    const steps = [item.step_fetch, item.step_analyze, item.step_resume, item.step_db, item.step_done]
    const done = steps.filter(s => s === 1).length
    if (done === 0) return 'processing'
    if (done === 1) return 'fetching'
    if (done === 2) return 'analyzing'
    if (done === 3) return 'resumed'
    if (done === 4) return 'saving'
    return 'processing'
  }
  return 'queued'
}

function PendingItem({ item, onDelete, onProcess, onReset, onDragStart, onViewWorkflow }) {
  const [processing, setProcessing] = useState(false)
  const statusKey = getProcessingStatus(item)
  const sc = STATUS_BADGE[statusKey]
  const steps = [item.step_fetch, item.step_analyze, item.step_resume, item.step_db, item.step_done]
  const done = steps.filter(s => s === 1).length
  const isProcessing = statusKey !== 'queued' && statusKey !== 'done' && statusKey !== 'failed'
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
      className="rounded-xl border overflow-hidden transition-all duration-200 hover:shadow-lg" style={{background:'var(--surface)',borderColor:'var(--border)',cursor: onDragStart ? 'grab' : 'default'}}>
      {/* Header row */}
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-center gap-2 mb-2">
          {/* Status badge */}
          <span className="inline-flex items-center gap-1 text-[0.6rem] font-bold px-2.5 py-1 rounded-full uppercase tracking-wide"
            style={{background:sc.bg,border:`1px solid ${sc.border}`,color:sc.fg,animation:sc.pulse?'pulse 2s ease-in-out infinite':'none'}}>
            <span className="text-xs">{sc.icon}</span>{item.status === 'done' ? 'Completed' : item.status === 'failed' ? 'Process Failed' : statusKey}
          </span>
          {/* Source badge */}
          <span className="text-[0.55rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
            style={{background:item.source==='web'?'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.15))':'var(--surface2)',border:item.source==='web'?'1px solid rgba(99,102,241,0.3)':'1px solid var(--border)',color:item.source==='web'?'var(--accent)':'var(--text-dim)'}}>
            {item.source==='web'?'🌐 Web':'⌨️ CLI'}
          </span>
          {item.company && <span className="text-xs font-bold" style={{color:'var(--text)'}}>{item.company}</span>}
          {item.job_num && <span className="text-[0.65rem] font-bold px-1.5 py-0.5 rounded" style={{background:'var(--accent)',color:'white'}}>#{item.job_num}</span>}
          <span className="text-[0.6rem] ml-auto" style={{color:'var(--text-dim)'}}>{new Date(item.created_at).toLocaleDateString()}</span>
          {onProcess && statusKey === 'queued' && <button onClick={handleProcess} disabled={processing}
            className="h-7 px-3 rounded-full flex items-center gap-1.5 text-[0.6rem] font-bold transition disabled:opacity-60"
            style={{background:'linear-gradient(135deg, #10b981, #06b6d4)',color:'white',boxShadow:'0 0 8px rgba(16,185,129,0.3)'}}>
            🚀 Process
          </button>}
          {isProcessing && (
            <div className="flex items-center gap-1">
              <span className="h-6 px-2 rounded-full flex items-center gap-1 text-[0.55rem] font-bold"
                style={{background:'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.15))',border:'1px solid rgba(99,102,241,0.3)',color:'var(--accent)'}}>
                <span className="animate-spin">⏳</span> Running
              </span>
              {onProcess && <button onClick={handleProcess} title="Reprocess from current step"
                className="w-6 h-6 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-green-500/20"
                style={{border:'1px solid rgba(34,197,94,0.4)',color:'#22c55e'}}>🔄</button>}
              {onReset && <button onClick={onReset} title="Stop & move to Queue"
                className="w-6 h-6 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-yellow-500/20"
                style={{border:'1px solid rgba(234,179,8,0.4)',color:'#eab308'}}>⏸</button>}
              {onDelete && <button onClick={onDelete} title="Remove completely"
                className="w-6 h-6 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}>🗑</button>}
            </div>
          )}
          {onProcess && statusKey === 'failed' && <button onClick={handleProcess} disabled={processing}
            className="h-7 px-3 rounded-full flex items-center gap-1.5 text-[0.6rem] font-bold transition disabled:opacity-60"
            style={{background:'linear-gradient(135deg, #f97316, #ef4444)',color:'white',boxShadow:'0 0 8px rgba(249,115,22,0.3)'}}>
            <span className={processing ? 'animate-spin' : ''}>🔁</span>{processing ? 'Retrying...' : 'Retry'}
          </button>}
          {statusKey === 'failed' && onDelete && <button onClick={onDelete} title="Remove completely"
            className="w-6 h-6 rounded-full flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
            style={{border:'1px solid rgba(239,68,68,0.4)',color:'var(--red)'}}>🗑</button>}
          {item.workflow_log && JSON.parse(item.workflow_log).length > 0 && (
            <button onClick={()=>onViewWorkflow && onViewWorkflow(item)} title="View workflow log"
              className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10"
              style={{border:'1px solid var(--border)',color:'var(--text-dim)'}}>📄</button>
          )}
        </div>
        {/* Title & Company */}
        {(item.title || item.company) && (
          <div className="px-1 mb-1">
            {item.title && <div className="text-xs font-bold truncate" style={{color:'var(--text)'}}>{item.title}</div>}
            {item.company && item.company !== item.title && <div className="text-[0.6rem] truncate" style={{color:'var(--text-dim)'}}>{item.company}</div>}
          </div>
        )}
        {/* URL */}
        <div className="text-[0.55rem] truncate mb-2 px-1" style={{color:'var(--text-dim)',opacity:0.6}}>{item.url}</div>
      </div>

      {/* Steps pipeline */}
      <div className="px-3 pb-3">
        <div className="flex items-center justify-between gap-0.5 p-2 rounded-lg" style={{background:'var(--surface2)'}}>
          {STEPS.map((step, i) => {
            const d = steps[i] === 1
            const isActive = i === nextStep && !d && item.status !== 'done' && item.status !== 'failed'
            return (
              <div key={step.key} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-0.5 flex-1">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center text-[0.7rem] transition-all duration-300"
                    style={{
                      background: d ? 'linear-gradient(135deg, #22c55e, #16a34a)' : isActive ? 'linear-gradient(135deg, var(--accent), var(--purple))' : 'var(--surface)',
                      color: d || isActive ? 'white' : 'var(--text-dim)',
                      boxShadow: d ? '0 0 8px rgba(34,197,94,0.4)' : isActive ? '0 0 8px rgba(99,102,241,0.4)' : 'none',
                      border: `1.5px solid ${d ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--border)'}`,
                      animation: isActive ? 'pulse 1.5s ease-in-out infinite' : 'none'
                    }}>
                    {d ? '✓' : isActive ? <span className="animate-spin">⏳</span> : step.icon}
                  </div>
                  <span className="text-[0.5rem] font-semibold" style={{color: d ? '#22c55e' : isActive ? 'var(--accent)' : 'var(--text-dim)'}}>{step.label}</span>
                </div>
                {i < 4 && (
                  <div className="h-[2px] flex-1 -mt-3 mx-0.5 rounded-full transition-all duration-300"
                    style={{background: d ? 'linear-gradient(90deg, #22c55e, #22c55e)' : 'var(--border)'}} />
                )}
              </div>
            )
          })}
        </div>
        {/* Progress counter */}
        <div className="flex items-center justify-between mt-2">
          <div className="text-[0.6rem] font-semibold" style={{color:'var(--text-dim)'}}>
            {done}/5 steps completed
          </div>
          <div className="flex gap-1">
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
            <span className="text-sm shrink-0">⚠️</span>
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

function JobCard({ job, onClick }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const cc = CITY_COLORS[job.location] || DEFAULT_CITY_COLOR
  const vs = VISA_STYLES[job.visa] || VISA_STYLES['Uncertain']
  return (
    <div onClick={onClick} className="rounded-lg p-3 border-l-3 cursor-pointer transition hover:shadow-lg hover:-translate-y-0.5" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftColor:job.score>=75?'var(--green)':job.score>=50?'var(--yellow)':'var(--red)'}}>
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
        <Tag>{job.work_type==='Remote'?'🏠':job.work_type==='Hybrid'?'🔄':'🏢'} {job.work_type}</Tag>
        <Tag className={getMatchClass(job.match)}>{job.match}</Tag>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:vs.bg,color:vs.text}}>{vs.label}</span>
        <Tag>👥 {job.applicants}</Tag>
      </div>
      <div className="text-xs pt-2 border-t" style={{color:'var(--text-dim)',borderColor:'var(--border)'}}><b style={{color:'var(--text)'}}>Stack:</b> {job.stack}</div>
    </div>
  )
}

function ScoreCard({ job, rank, onClick, onRescore, onDelete, onRequeue, onViewWorkflow }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const cc = CITY_COLORS[job.location] || DEFAULT_CITY_COLOR
  const vs = VISA_STYLES[job.visa] || VISA_STYLES['Uncertain']
  const hasLogs = job.workflow_log && JSON.parse(job.workflow_log).length > 0
  return (
    <div className="rounded-lg p-3 border-l-3 transition hover:shadow-lg hover:-translate-y-0.5" style={{background:'var(--surface)',borderColor:'var(--border)',borderLeftColor:job.score>=75?'var(--green)':job.score>=50?'var(--yellow)':'var(--red)'}}>
      <div className="flex justify-between items-center mb-1">
        <span onClick={onClick} className="cursor-pointer"><span className={`text-xs font-semibold ${rank<=3?'text-[var(--accent)]':''}`} style={{color:rank>3?'var(--text-dim)':undefined}}>#{rank}</span></span>
        <div className="flex items-center gap-1">
          {hasLogs && onViewWorkflow && <button onClick={(e)=>{e.stopPropagation();onViewWorkflow({id:job.num,workflow_log:job.workflow_log,company:job.company,job_num:job.num})}} title="View workflow log" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}>📄</button>}
          {onRescore && <button onClick={(e)=>{e.stopPropagation();onRescore(job.num)}} title="Rescore this job" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-white/10" style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}>🔃</button>}
          {onRequeue && <button onClick={(e)=>{e.stopPropagation();onRequeue(job.num)}} title="Re-queue for processing (old version hidden)" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-blue-500/20" style={{color:'var(--blue, #3b82f6)',border:'1px solid rgba(59,130,246,0.3)'}}>🔄</button>}
          {onDelete && <button onClick={(e)=>{e.stopPropagation();onDelete(job.num)}} title="Hide this job" className="w-5 h-5 rounded flex items-center justify-center text-[0.55rem] transition hover:bg-red-500/20" style={{color:'var(--red)',border:'1px solid rgba(239,68,68,0.3)'}}>🗑</button>}
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
        <Tag>{job.work_type==='Remote'?'🏠':job.work_type==='Hybrid'?'🔄':'🏢'} {job.work_type}</Tag>
        <Tag className={getMatchClass(job.match)}>{job.match}</Tag>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] font-semibold" style={{background:vs.bg,color:vs.text}}>{vs.label}</span>
        <Tag>👥 {job.applicants}</Tag>
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
  const categoryIcons = { scoring: '📊', tech: '💻', domain: '🏢', visa: '🛂', strategy: '🎯' }

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
        <div className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
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
        <div key={cat} className="rounded-xl border p-4" style={{background:'var(--surface)',borderColor:'var(--border)'}}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">{categoryIcons[cat] || '⚙️'}</span>
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
                      style={{color:'var(--text-dim)',border:'1px solid var(--border)'}}>✏️</button>
                    <button onClick={() => handleDelete(pref.id)}
                      className="w-6 h-6 rounded flex items-center justify-center text-[0.6rem] transition hover:bg-red-500/20"
                      style={{color:'var(--red)',border:'1px solid rgba(239,68,68,0.3)'}}>🗑</button>
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
