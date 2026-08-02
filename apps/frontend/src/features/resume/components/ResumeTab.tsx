import { useState, useEffect } from 'react'
import { FileText, LinkedinLogo, Star, Upload, Trash, Warning } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Card, CardContent } from '@/shared/ui/card'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Textarea } from '@/shared/ui/textarea'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/shared/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/shared/ui/dialog'
import ResumePreview from '@/shared/components/ResumePreview'

const API = '/api'

function showToast(msg) {
  window.dispatchEvent(new CustomEvent('toast', { detail: msg }))
}

export default function ResumeTab({ resumes, linkedinProfiles, onRefreshResumes, onRefreshLinkedin }) {
  const [viewingItem, setViewingItem] = useState(null)
  const [subTab, setSubTab] = useState('resume')

  // Resume upload states
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadText, setUploadText] = useState('')
  const [uploadSaving, setUploadSaving] = useState(false)

  // LinkedIn upload states
  const [linkedinUploadOpen, setLinkedinUploadOpen] = useState(false)
  const [linkedinUploadText, setLinkedinUploadText] = useState('')
  const [linkedinUploadSaving, setLinkedinUploadSaving] = useState(false)

  const originalResumes = resumes.filter(r => r.id?.startsWith('original_')).sort((a, b) => (b.version || 0) - (a.version || 0))
  const latestResume = originalResumes[0]

  const sortedProfiles = linkedinProfiles.filter(p => p.id?.startsWith('linkedin_')).sort((a, b) => (b.version || 0) - (a.version || 0))
  const latestProfile = sortedProfiles[0]

  // ─── Resume handlers ───
  const handleResumeUpload = async () => {
    if (!uploadText.trim()) return
    setUploadSaving(true)
    try {
      const res = await fetch(`${API}/resumes`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: uploadText })
      })
      const data = await res.json()
      if (data.status === 'saved') {
        showToast(`Resume v${data.version} saved`)
        setUploadOpen(false); setUploadText(''); onRefreshResumes()
      }
    } finally { setUploadSaving(false) }
  }

  const handleDeleteResume = async (version) => {
    await fetch(`${API}/resumes/${version}`, { method: 'DELETE' })
    if (viewingItem?.id === `original_${version}`) setViewingItem(null)
    showToast('Resume deleted'); onRefreshResumes()
  }

  // ─── LinkedIn handlers ───
  const handleLinkedinUpload = async () => {
    if (!linkedinUploadText.trim()) return
    setLinkedinUploadSaving(true)
    try {
      const res = await fetch(`${API}/linkedin`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: linkedinUploadText })
      })
      const data = await res.json()
      if (data.status === 'saved') {
        showToast(`LinkedIn Profile v${data.version} saved`)
        setLinkedinUploadOpen(false); setLinkedinUploadText(''); onRefreshLinkedin()
      }
    } finally { setLinkedinUploadSaving(false) }
  }

  const handleDeleteLinkedin = async (version) => {
    await fetch(`${API}/linkedin/${version}`, { method: 'DELETE' })
    if (viewingItem?.id === `linkedin_${version}`) setViewingItem(null)
    showToast('Profile deleted'); onRefreshLinkedin()
  }

  const currentItems = subTab === 'resume' ? originalResumes : sortedProfiles
  const hasPreview = !!viewingItem

  // Auto-select first (latest) item when switching tabs or when data changes
  useEffect(() => {
    if (subTab === 'resume' && originalResumes.length > 0) {
      if (!viewingItem || !originalResumes.find(r => r.id === viewingItem.id)) {
        setViewingItem(originalResumes[0])
      }
    } else if (subTab === 'linkedin' && sortedProfiles.length > 0) {
      if (!viewingItem || !sortedProfiles.find(p => p.id === viewingItem.id)) {
        setViewingItem(sortedProfiles[0])
      }
    }
  }, [subTab, resumes, linkedinProfiles])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <FileText className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-extrabold">Profile & Resume</h2>
      </div>

      <Tabs value={subTab} onValueChange={(v) => { setSubTab(v); setViewingItem(null) }}>
        <TabsList className="bg-muted">
          <TabsTrigger value="resume" className="gap-1.5 text-2xs">
            <Star className="w-3.5 h-3.5" />
            Resumes
            {originalResumes.length > 0 && <Badge variant="outline" className="ml-1 text-2xs h-4">{originalResumes.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="linkedin" className="gap-1.5 text-2xs">
            <LinkedinLogo className="w-3.5 h-3.5" />
            LinkedIn Profile
            {sortedProfiles.length > 0 && <Badge variant="outline" className="ml-1 text-2xs h-4">{sortedProfiles.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* ─── RESUMES TAB ─── */}
        <TabsContent value="resume">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-muted-foreground">
              Your base resumes used for processing and generating tailored versions
            </span>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setUploadOpen(true)}>
              <Upload className="w-3.5 h-3.5" /> Upload Resume
            </Button>
          </div>

          {originalResumes.length === 0 && !hasPreview ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No resumes uploaded yet.</p>
                <p className="text-xs mt-1">Upload your base resume — it's used to score jobs and generate tailored versions.</p>
                <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={() => setUploadOpen(true)}>
                  <Upload className="w-3.5 h-3.5" /> Upload Resume
                </Button>
              </CardContent>
            </Card>
          ) : (
            <ResumeListView
              items={originalResumes}
              viewingItem={viewingItem}
              onSelect={setViewingItem}
              onDelete={handleDeleteResume}
              renderItem={(r) => ({ label: `v${r.version}`, sub: r.created_at ? new Date(r.created_at).toLocaleDateString() : '' })}
              renderBadge={(r, i) => i === 0 && <Badge variant="default" className="text-3xs h-3.5 px-1">Active</Badge>}
            />
          )}
        </TabsContent>

        {/* ─── LINKEDIN TAB ─── */}
        <TabsContent value="linkedin">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-muted-foreground">
              LinkedIn profile — used as additional context during job analysis and scoring
            </span>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setLinkedinUploadOpen(true)}>
              <Upload className="w-3.5 h-3.5" /> Upload Profile
            </Button>
          </div>

          <div className="flex items-start gap-2 mb-3 p-2.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <Warning className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-500/80">
              Personal info (name, phone, email, LinkedIn URL) is automatically masked for privacy.
            </p>
          </div>

          {sortedProfiles.length === 0 && !hasPreview ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <LinkedinLogo className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No LinkedIn profile uploaded yet.</p>
                <p className="text-xs mt-1">Paste your LinkedIn profile text to give the AI more context about your experience.</p>
                <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={() => setLinkedinUploadOpen(true)}>
                  <Upload className="w-3.5 h-3.5" /> Upload Profile
                </Button>
              </CardContent>
            </Card>
          ) : (
            <ResumeListView
              items={sortedProfiles}
              viewingItem={viewingItem}
              onSelect={setViewingItem}
              onDelete={handleDeleteLinkedin}
              renderItem={(p) => ({ label: `v${p.version}`, sub: p.created_at ? new Date(p.created_at).toLocaleDateString() : '' })}
              renderBadge={(p, i) => i === 0 && <Badge variant="default" className="text-3xs h-3.5 px-1">Active</Badge>}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* ─── Upload Resume Dialog ─── */}
      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-primary" />
              Upload Resume
            </DialogTitle>
            <DialogDescription>
              Paste your resume text below. This becomes your base resume used for processing and generating tailored versions.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={uploadText}
            onChange={e => setUploadText(e.target.value)}
            placeholder={"Paste your resume content here...\n\nPersonal info (name, phone, email) will be automatically masked for privacy."}
            className="h-[250px] font-mono text-xs resize-none"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => { setUploadOpen(false); setUploadText('') }}>Cancel</Button>
            <Button onClick={handleResumeUpload} disabled={uploadSaving || !uploadText.trim()}>
              {uploadSaving ? 'Saving...' : 'Save Resume'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ─── Upload LinkedIn Dialog ─── */}
      <Dialog open={linkedinUploadOpen} onOpenChange={setLinkedinUploadOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-[#0A66C2]" />
              Upload LinkedIn Profile
            </DialogTitle>
            <DialogDescription>
              Paste your LinkedIn profile text below. This provides additional context for better job matching.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={linkedinUploadText}
            onChange={e => setLinkedinUploadText(e.target.value)}
            placeholder={"Paste your LinkedIn profile text here...\n\nInclude: About, Experience, Education, Skills, Recommendations\n\nPersonal info will be automatically masked for privacy."}
            className="h-[250px] font-mono text-xs resize-none"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => { setLinkedinUploadOpen(false); setLinkedinUploadText('') }}>Cancel</Button>
            <Button onClick={handleLinkedinUpload} disabled={linkedinUploadSaving || !linkedinUploadText.trim()}>
              {linkedinUploadSaving ? 'Saving...' : 'Save Profile'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Reusable list+preview component
function ResumeListView({ items, viewingItem, onSelect, onDelete, renderItem, renderBadge }) {
  return (
    <div className="flex gap-3 h-[calc(100vh-240px)] overflow-hidden">
      <div className={cn(
        "shrink-0 flex flex-col transition-all duration-300 overflow-hidden",
        viewingItem ? "w-[220px]" : "w-[280px]"
      )}>
        <Card className="flex-1 flex flex-col min-h-0">
          <CardContent className="flex-1 min-h-0 p-2">
            <ScrollArea className="h-full">
              <div className="space-y-0.5">
                {items.map((item, i) => {
                  const { label, sub } = renderItem(item)
                  return (
                    <div key={item.id} className={cn(
                      "flex items-center gap-2 px-2.5 py-2 rounded-md transition cursor-pointer text-left w-full",
                      viewingItem?.id === item.id ? "bg-primary/10 ring-1 ring-primary" : "hover:bg-muted"
                    )} onClick={() => onSelect(item)}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold truncate">{label}</span>
                          {renderBadge(item, i)}
                        </div>
                        <div className="text-2xs text-muted-foreground truncate">{sub}</div>
                      </div>
                      <button
                        className="shrink-0 w-5 h-5 rounded flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition"
                        onClick={(e) => { e.stopPropagation(); onDelete(item.version) }}
                        title="Delete"
                      >
                        <Trash className="w-3 h-3" />
                      </button>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 min-w-0 overflow-hidden">
        {viewingItem ? (
          <Card className="h-full flex flex-col min-h-0">
            <div className="px-4 pt-3 pb-2 flex items-center justify-between shrink-0">
              <span className="text-sm font-bold">{viewingItem.title || 'Preview'}</span>
              <Button variant="ghost" size="sm" className="h-6 text-2xs" onClick={() => onSelect(null)}>Close</Button>
            </div>
            <CardContent className="flex-1 min-h-0 overflow-hidden flex flex-col items-center">
              <div className="flex-1 min-h-0 w-full flex items-start justify-center overflow-y-auto">
                <ResumePreview html={viewingItem.content} className="shadow-lg mx-auto" />
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex items-center justify-center text-muted-foreground text-sm">
            Click an item on the left to preview it here
          </Card>
        )}
      </div>
    </div>
  )
}
