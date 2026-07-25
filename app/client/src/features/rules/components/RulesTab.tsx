import { useState } from 'react'
import { PencilSimple, Trash, Check, X, Plus, ArrowUp, ArrowDown, Target, DotsSixVertical, Users, Buildings, Briefcase, Handshake } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Input } from '@/shared/ui/input'
import { Switch } from '@/shared/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy, arrayMove } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

const API = '/api'

const SCOPE_CONFIG = {
  SHARED: { label: 'Shared', color: 'bg-purple-500/15 text-purple-500 border-purple-500/30', icon: <Users className="w-4 h-4" />, header: 'text-purple-500', headerBg: 'bg-purple-500/5', headerBorder: 'border-purple-500/20', desc: 'Applied to all entity types' },
  JOB: { label: 'Job', color: 'bg-blue-500/15 text-blue-500 border-blue-500/30', icon: <Briefcase className="w-4 h-4" />, header: 'text-blue-500', headerBg: 'bg-blue-500/5', headerBorder: 'border-blue-500/20', desc: 'Applied only to job scoring' },
  COMPANY_PRODUCT: { label: 'Product Company', color: 'bg-green-500/15 text-green-500 border-green-500/30', icon: <Buildings className="w-4 h-4" />, header: 'text-green-500', headerBg: 'bg-green-500/5', headerBorder: 'border-green-500/20', desc: 'Applied to product/engineering companies' },
  COMPANY_RECRUITING: { label: 'Recruiting', color: 'bg-orange-500/15 text-orange-500 border-orange-500/30', icon: <Handshake className="w-4 h-4" />, header: 'text-orange-500', headerBg: 'bg-orange-500/5', headerBorder: 'border-orange-500/20', desc: 'Applied to recruiting/staffing companies' },
}

const FILTER_TABS = [
  { id: 'all', label: 'All' },
  { id: 'SHARED', label: 'Shared' },
  { id: 'JOB', label: 'Jobs' },
  { id: 'COMPANY_PRODUCT', label: 'Product Company' },
  { id: 'COMPANY_RECRUITING', label: 'Recruiting' },
]

function PriorityBadge({ p }) {
  if (p >= 90) return <Badge className="text-2xs px-1 h-3.5 bg-red-500/15 text-red-500 border-red-500/30 shrink-0">Critical</Badge>
  if (p >= 75) return <Badge className="text-2xs px-1 h-3.5 bg-orange-500/15 text-orange-500 border-orange-500/30 shrink-0">High</Badge>
  if (p >= 50) return <Badge variant="secondary" className="text-2xs px-1 h-3.5 shrink-0">Med</Badge>
  return <Badge variant="outline" className="text-2xs px-1 h-3.5 shrink-0">Low</Badge>
}

function ScopeBadge({ scope }) {
  const config = SCOPE_CONFIG[scope] || SCOPE_CONFIG.SHARED
  return <Badge variant="outline" className={cn("text-3xs px-0.5 h-2.5 shrink-0", config.color)}>{config.label}</Badge>
}

function RuleForm({ initial, onSave, onCancel }) {
  const [f, setF] = useState(initial || { category: 'fit', scope: 'JOB', key: '', value: '', description: '', priority: 50, score_weight: 50 })
  return (
    <div className="p-3 rounded-lg border border-dashed bg-muted/30 space-y-2">
      <div className="grid grid-cols-4 gap-2">
        <Select value={f.scope} onValueChange={(v) => setF({ ...f, scope: v })}>
          <SelectTrigger className="h-7 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="SHARED">Shared (ALL)</SelectItem>
            <SelectItem value="JOB">Job</SelectItem>
            <SelectItem value="COMPANY_PRODUCT">Product Company</SelectItem>
            <SelectItem value="COMPANY_RECRUITING">Recruiting</SelectItem>
          </SelectContent>
        </Select>
        <Select value={f.category} onValueChange={(v) => setF({ ...f, category: v })}>
          <SelectTrigger className="h-7 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="fit">Fit score</SelectItem>
            <SelectItem value="success">Success score</SelectItem>
          </SelectContent>
        </Select>
        <Input value={f.key} onChange={e => setF({ ...f, key: e.target.value })} placeholder="Key name" className="h-7 text-xs" />
        <div className="flex items-center gap-1">
          <span className="text-2xs text-muted-foreground shrink-0">W:</span>
          <Input type="number" min="0" max="100" value={f.score_weight} onChange={e => setF({ ...f, score_weight: parseInt(e.target.value) || 0 })} className="h-7 text-xs flex-1" />
        </div>
      </div>
      <Textarea value={f.value} onChange={e => setF({ ...f, value: e.target.value })} placeholder="Value / rule" className="text-xs min-h-[48px]" />
      <Input value={f.description} onChange={e => setF({ ...f, description: e.target.value })} placeholder="How this affects scoring (optional)" className="h-7 text-xs" />
      <div className="flex gap-1">
        <Button size="sm" className="h-6 text-2xs bg-green-500 hover:bg-green-600 gap-0.5" onClick={() => { if (f.key && f.value) onSave(f) }}><Check className="w-2.5 h-2.5" /> Save</Button>
        <Button size="sm" variant="ghost" className="h-6 text-2xs gap-0.5" onClick={onCancel}><X className="w-2.5 h-2.5" /> Cancel</Button>
      </div>
    </div>
  )
}

function SortableRule({ pref, idx, editing, onEdit, onSave, onCancel, onToggle, onDelete, onPriority }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: pref.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
    opacity: isDragging ? 0.8 : undefined,
  }

  return (
    <div ref={setNodeRef} style={style} className={cn("rounded-lg transition hover:bg-muted/50 group", !pref.enabled && "opacity-40", isDragging && "ring-2 ring-primary/30 shadow-lg")}>
      {editing === pref.id ? (
        <div className="p-1">
          <RuleForm initial={pref} onSave={(form) => onSave(pref.id, form)} onCancel={onCancel} />
        </div>
      ) : (
        <div className="flex items-start gap-1.5 p-1.5">
          <div {...attributes} {...listeners} className="shrink-0 mt-0.5 cursor-grab active:cursor-grabbing text-muted-foreground/50 hover:text-muted-foreground transition">
            <DotsSixVertical className="w-3 h-3" />
          </div>
          <Switch checked={!!pref.enabled} onCheckedChange={(c) => onToggle(pref.id, c)} className="scale-75 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-2xs text-muted-foreground w-3 text-right shrink-0">{idx + 1}.</span>
              <span className="text-xs font-semibold truncate">{pref.key}</span>
              <Badge variant="outline" className="text-3xs px-0.5 h-2.5 shrink-0">{pref.category}</Badge>
              <ScopeBadge scope={pref.scope} />
              <PriorityBadge p={pref.priority} />
              <span className="text-2xs text-muted-foreground">w:{pref.score_weight || pref.priority}</span>
            </div>
            <div className="text-2xs text-muted-foreground mt-0.5 ml-4">{pref.value}</div>
            {pref.description && <div className="text-2xs text-muted-foreground/60 mt-0.5 ml-4 italic">{pref.description}</div>}
          </div>
          <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition">
            <Button variant="ghost" size="icon" className="h-4 w-4" onClick={() => onPriority(pref.id, 5, pref.priority)} title="Priority +5"><ArrowUp className="w-2 h-2" /></Button>
            <Button variant="ghost" size="icon" className="h-4 w-4" onClick={() => onPriority(pref.id, -5, pref.priority)} title="Priority -5"><ArrowDown className="w-2 h-2" /></Button>
            <Button variant="ghost" size="icon" className="h-4 w-4" onClick={() => onEdit(pref.id)} title="Edit"><PencilSimple className="w-2 h-2" /></Button>
            <Button variant="ghost" size="icon" className="h-4 w-4 text-destructive hover:text-destructive" onClick={() => onDelete(pref.id)} title="Delete"><Trash className="w-2 h-2" /></Button>
          </div>
        </div>
      )}
    </div>
  )
}

function RuleColumn({ scope, prefs, editing, onEdit, onSave, onCancel, onToggle, onDelete, onPriority, onAdd, onReorder, showAdd, setShowAdd }) {
  const meta = SCOPE_CONFIG[scope]
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const ids = prefs.map(p => p.id)

  const handleDragEnd = (event) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = prefs.findIndex(p => p.id === active.id)
    const newIndex = prefs.findIndex(p => p.id === over.id)
    const reordered = arrayMove(prefs, oldIndex, newIndex)
    onReorder(scope, reordered)
  }

  return (
    <div className="flex flex-col min-w-0">
      <div className={cn("flex items-center gap-2 px-3 py-2 rounded-t-lg border border-b-0", meta.headerBg, meta.headerBorder)}>
        <span className={meta.header}>{meta.icon}</span>
        <span className={cn("text-sm font-bold", meta.header)}>{meta.label} Rules</span>
        <Badge variant="secondary" className="text-2xs ml-auto">{prefs.filter(p => p.enabled).length}/{prefs.length}</Badge>
      </div>
      <div className={cn("rounded-b-lg border p-2 space-y-0.5 max-h-[600px] overflow-y-auto", meta.headerBorder)}>
        <div className="text-2xs text-muted-foreground mb-1">{meta.desc}</div>
        <Button variant="ghost" size="sm" className="h-6 text-2xs gap-0.5 text-muted-foreground w-full justify-start" onClick={() => setShowAdd(showAdd ? null : scope)}>
          <Plus className="w-2.5 h-2.5" /> Add rule
        </Button>
        {showAdd === scope && (
          <RuleForm initial={{ category: 'fit', scope: scope, key: '', value: '', description: '', priority: 50, score_weight: 50 }} onSave={(form) => { onAdd(form); setShowAdd(null) }} onCancel={() => setShowAdd(null)} />
        )}
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={ids} strategy={verticalListSortingStrategy}>
            {prefs.map((pref, idx) => (
              <SortableRule key={pref.id} pref={pref} idx={idx} editing={editing}
                onEdit={onEdit} onSave={onSave} onCancel={onCancel}
                onToggle={onToggle} onDelete={onDelete} onPriority={onPriority} />
            ))}
          </SortableContext>
        </DndContext>
      </div>
    </div>
  )
}

export default function RulesTab({ rules, onUpdate }) {
  const [editing, setEditing] = useState(null)
  const [showAdd, setShowAdd] = useState(null)
  const [filter, setFilter] = useState('all')

  const api = async (method, path, body) => {
    await fetch(`${API}${path}`, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
    onUpdate()
  }

  const handleSave = async (id, form) => { await api('PUT', `/rules/${id}`, { value: form.value, description: form.description, score_weight: form.score_weight, scope: form.scope }); setEditing(null) }
  const handleToggle = async (id, enabled) => api('PUT', `/rules/${id}`, { enabled: enabled ? 1 : 0 })
  const handleDelete = async (id) => api('DELETE', `/rules/${id}`)
  const handleAdd = async (form) => { await api('POST', '/rules', { rules: [{ ...form, rule_type: form.scope === 'SHARED' ? 'shared' : form.scope === 'JOB' ? 'job' : form.scope === 'COMPANY_PRODUCT' ? 'company' : 'recruiter' }] }) }
  const handlePriority = async (id, delta, current) => api('PUT', `/rules/${id}`, { priority: Math.max(0, Math.min(100, current + delta)) })

  const handleReorder = async (scope, reordered) => {
    const total = reordered.length
    const updates = reordered.map((rule, i) => {
      const newPriority = Math.max(1, Math.round(100 - (i / Math.max(total - 1, 1)) * 99))
      return api('PUT', `/rules/${rule.id}`, { priority: newPriority })
    })
    await Promise.all(updates)
  }

  if (!rules) return <div className="text-center py-12 text-muted-foreground">Loading rules...</div>

  // Group rules by scope
  const allRules = []
  const scopeGroups = {}
  for (const [scope, items] of Object.entries(rules)) {
    const sorted = (items || []).sort((a, b) => b.priority - a.priority)
    scopeGroups[scope] = sorted
    allRules.push(...sorted)
  }

  const total = allRules.length
  const enabled = allRules.filter(r => r.enabled).length

  // Filter rules based on active filter
  const getFilteredScopes = () => {
    if (filter === 'all') return Object.keys(SCOPE_CONFIG)
    return [filter]
  }

  const filteredScopes = getFilteredScopes().filter(s => scopeGroups[s]?.length > 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold">Scoring Rules</h2>
          <p className="text-xs text-muted-foreground">{enabled}/{total} active — Shared rules apply to all entity types</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-1">
        {FILTER_TABS.map(tab => {
          const count = tab.id === 'all' ? total : (scopeGroups[tab.id]?.length || 0)
          return (
            <Button
              key={tab.id}
              variant={filter === tab.id ? 'default' : 'outline'}
              size="sm"
              className={cn("h-6 text-2xs gap-1", filter === tab.id && "bg-primary text-primary-foreground")}
              onClick={() => setFilter(tab.id)}
            >
              {tab.label}
              <span className="text-2xs opacity-70">({count})</span>
            </Button>
          )
        })}
      </div>

      {/* Rule columns */}
      <div className={cn("gap-3", filteredScopes.length <= 3 ? "grid grid-cols-3" : filteredScopes.length <= 4 ? "grid grid-cols-4" : "grid grid-cols-3")}>
        {filteredScopes.map(scope => (
          <RuleColumn key={scope} scope={scope} prefs={scopeGroups[scope] || []} editing={editing} showAdd={showAdd} setShowAdd={setShowAdd}
            onEdit={setEditing} onSave={handleSave} onCancel={() => setEditing(null)}
            onToggle={handleToggle} onDelete={handleDelete} onPriority={handlePriority} onAdd={handleAdd} onReorder={handleReorder} />
        ))}
      </div>
    </div>
  )
}
