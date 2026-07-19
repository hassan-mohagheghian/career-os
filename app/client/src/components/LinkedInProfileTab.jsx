import { useState, useEffect } from 'react'
import { LinkedinLogo, Upload, Trash, Eye, Warning } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import ResumePreview from '@/components/ResumePreview'

const API = '/api'

export default function LinkedInProfileTab({ profiles, onRefresh }) {
  const [toast, setToast] = useState(null)
  const [viewingProfile, setViewingProfile] = useState(null)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadText, setUploadText] = useState('')
  const [uploadSaving, setUploadSaving] = useState(false)

  const sortedProfiles = profiles
    .filter(p => p.id?.startsWith('linkedin_'))
    .sort((a, b) => (b.version || 0) - (a.version || 0))
  const latestProfile = sortedProfiles[0]

  // Auto-select first (latest) profile when data changes
  useEffect(() => {
    if (sortedProfiles.length > 0 && (!viewingProfile || !sortedProfiles.find(p => p.id === viewingProfile.id))) {
      setViewingProfile(sortedProfiles[0])
    }
  }, [profiles])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(null), 2000) }

  const handleUpload = async () => {
    if (!uploadText.trim()) return
    setUploadSaving(true)
    try {
      const res = await fetch(`${API}/linkedin`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: uploadText })
      })
      const data = await res.json()
      if (data.status === 'saved') {
        showToast(`LinkedIn Profile v${data.version} saved`)
        setUploadOpen(false)
        setUploadText('')
        onRefresh()
      }
    } finally { setUploadSaving(false) }
  }

  const handleDelete = async (version) => {
    await fetch(`${API}/linkedin/${version}`, { method: 'DELETE' })
    if (viewingProfile?.id === `linkedin_${version}`) setViewingProfile(null)
    showToast('Profile deleted')
    onRefresh()
  }

  return (
    <div className="space-y-4">
      {toast && <div className="fixed top-14 right-4 z-[200] px-3 py-1.5 rounded-lg text-xs font-bold bg-primary text-primary-foreground">{toast}</div>}

      <div className="flex items-center gap-3">
        <LinkedinLogo className="w-5 h-5 text-[#0A66C2]" />
        <h2 className="text-xl font-extrabold">LinkedIn Profile</h2>
        {latestProfile && <Badge variant="default">v{latestProfile.version}</Badge>}
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-muted-foreground">
          Your LinkedIn profile text — used as additional context during job analysis and scoring
        </span>
        <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setUploadOpen(true)}>
          <Upload className="w-3.5 h-3.5" />
          Upload Profile
        </Button>
      </div>

      <div className="flex items-start gap-2 mb-3 p-2.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
        <Warning className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
        <p className="text-[0.65rem] text-yellow-500/80">
          Personal info (name, phone, email, LinkedIn URL) is automatically masked for privacy.
          The raw text is used internally for better job matching — only the masked version is shown in the UI.
        </p>
      </div>

      {sortedProfiles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <LinkedinLogo className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No LinkedIn profile uploaded yet.</p>
            <p className="text-[0.65rem] mt-1">Paste your LinkedIn profile text to give the AI more context about your experience and skills.</p>
            <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={() => setUploadOpen(true)}>
              <Upload className="w-3.5 h-3.5" /> Upload Profile
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="flex gap-3 h-[calc(100vh-240px)] overflow-hidden">
          {/* Left: List */}
          <div className={cn(
            "shrink-0 flex flex-col transition-all duration-300 overflow-hidden",
            viewingProfile ? "w-[220px]" : "w-[280px]"
          )}>
            <Card className="flex-1 flex flex-col min-h-0">
              <CardContent className="flex-1 min-h-0 p-2">
                <ScrollArea className="h-full">
                  <div className="space-y-0.5">
                    {sortedProfiles.map((p, i) => (
                      <div key={p.id} className={cn(
                        "flex items-center gap-2 px-2.5 py-2 rounded-md transition cursor-pointer text-left w-full",
                        viewingProfile?.id === p.id
                          ? "bg-primary/10 ring-1 ring-primary"
                          : "hover:bg-muted"
                      )} onClick={() => setViewingProfile(p)}>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold truncate">v{p.version}</span>
                            {i === 0 && <Badge variant="default" className="text-[0.4rem] h-3.5 px-1">Active</Badge>}
                          </div>
                          <div className="text-[0.55rem] text-muted-foreground truncate">
                            {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                          </div>
                        </div>
                        <button
                          className="shrink-0 w-5 h-5 rounded flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition"
                          onClick={(e) => { e.stopPropagation(); handleDelete(p.version) }}
                          title="Delete profile"
                        >
                          <Trash className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Right: Preview */}
          <div className="flex-1 min-w-0 overflow-hidden">
            {viewingProfile ? (
              <Card className="h-full flex flex-col min-h-0">
                <CardHeader className="pb-2 shrink-0">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <LinkedinLogo className="w-4 h-4 text-[#0A66C2]" />
                      LinkedIn Profile v{viewingProfile.version}
                    </CardTitle>
                    <Button variant="ghost" size="sm" className="h-6 text-[0.55rem]" onClick={() => setViewingProfile(null)}>
                      Close
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 min-h-0 overflow-hidden flex flex-col items-center">
                  <div className="flex-1 min-h-0 w-full flex items-start justify-center overflow-y-auto">
                    <ResumePreview html={viewingProfile.content} className="shadow-lg mx-auto" />
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="h-full flex items-center justify-center text-muted-foreground text-sm">
                Click a profile on the left to preview it here
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-[#0A66C2]" />
              Upload LinkedIn Profile
            </DialogTitle>
            <DialogDescription>
              Paste your LinkedIn profile text below. This provides additional context about your experience, skills, and recommendations for better job matching.
            </DialogDescription>
          </DialogHeader>
          <div>
            <Textarea
              value={uploadText}
              onChange={e => setUploadText(e.target.value)}
              placeholder={"Paste your LinkedIn profile text here...\n\nInclude: About, Experience, Education, Skills, Recommendations\n\nPersonal info will be automatically masked for privacy."}
              className="h-[250px] font-mono text-xs resize-none"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setUploadOpen(false); setUploadText('') }}>Cancel</Button>
            <Button onClick={handleUpload} disabled={uploadSaving || !uploadText.trim()}>
              {uploadSaving ? 'Saving...' : 'Save Profile'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
