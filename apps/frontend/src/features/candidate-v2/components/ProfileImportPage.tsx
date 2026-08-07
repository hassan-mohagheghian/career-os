'use client'

import { useState, useCallback, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Upload, LinkSimple, GitBranch, CheckCircle, Sparkle, FileText } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card'
import { Badge } from '@/shared/ui/badge'
import { Textarea } from '@/shared/ui/textarea'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/shared/ui/tabs'
import { Separator } from '@/shared/ui/separator'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { PageHeader } from '@/shared/components/PageHeader'
import { resumeApi } from '@/entities/resume/api'
import { linkedinApi } from '@/entities/linkedin/api'
import {
  useCandidateProfileQuery,
  useCandidateSourcesQuery,
  useCandidateVersionsQuery,
  useAnalyzeProfileMutation,
} from '@/entities/candidate/hooks'
import type { CandidateProfile, CandidateSource, CandidateVersion } from '@/entities/candidate/types'

const PROFILE_KEY = 'candidate-profile'
const SOURCES_KEY = 'candidate-sources'
const VERSIONS_KEY = 'candidate-versions'

export function ProfileImportPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'sources' | 'review'>('sources')

  const [resumeText, setResumeText] = useState('')
  const [linkedinText, setLinkedinText] = useState('')
  const [githubUsername, setGithubUsername] = useState('')
  const [savingResume, setSavingResume] = useState(false)
  const [savingLinkedin, setSavingLinkedin] = useState(false)

  const profileQuery = useCandidateProfileQuery()
  const sourcesQuery = useCandidateSourcesQuery()
  const versionsQuery = useCandidateVersionsQuery()
  const analyzeMutation = useAnalyzeProfileMutation()

  const hasProfile = !!profileQuery.data
  const isAnalyzing = analyzeMutation.isPending
  const lastError = analyzeMutation.error ? errorMessage(analyzeMutation.error) : null

  const refreshProfile = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: [PROFILE_KEY] })
    queryClient.invalidateQueries({ queryKey: [SOURCES_KEY] })
    queryClient.invalidateQueries({ queryKey: [VERSIONS_KEY] })
  }, [queryClient])

  const handleSaveResume = useCallback(async () => {
    if (!resumeText.trim()) return
    setSavingResume(true)
    try {
      await resumeApi.upload(resumeText)
      setResumeText('')
      toast.success('Resume saved')
    } catch {
      toast.error('Failed to save resume')
    } finally {
      setSavingResume(false)
    }
  }, [resumeText])

  const handleSaveLinkedin = useCallback(async () => {
    if (!linkedinText.trim()) return
    setSavingLinkedin(true)
    try {
      await linkedinApi.upload(linkedinText)
      setLinkedinText('')
      toast.success('LinkedIn profile saved')
    } catch {
      toast.error('Failed to save LinkedIn profile')
    } finally {
      setSavingLinkedin(false)
    }
  }, [linkedinText])

  const handleAnalyze = useCallback(() => {
    analyzeMutation.mutate(undefined, {
      onSuccess: (result) => {
        toast.success('Profile analysis queued')
        setActiveTab('review')
        void result
      },
      onError: () => {
        toast.error('Failed to start profile analysis')
      },
    })
  }, [analyzeMutation])

  const sources = sourcesQuery.data?.items ?? []
  const versions = versionsQuery.data?.items ?? []

  const skills = useMemo(() => profileQuery.data?.skills ?? [], [profileQuery.data])
  const experiences = useMemo(() => profileQuery.data?.experiences ?? [], [profileQuery.data])
  const projects = useMemo(() => profileQuery.data?.projects ?? [], [profileQuery.data])

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col gap-4 p-4 md:p-6">
      <PageHeader title="Candidate Profile">Profile import and review</PageHeader>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'sources' | 'review')}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <SourceCard
              title="Resume"
              description="Paste your resume text. This becomes the base resume for your profile."
              icon={<FileText className="h-4 w-4 text-primary" />}
              value={resumeText}
              onChange={setResumeText}
              placeholder={'Paste your resume content here...'}
              actionLabel={savingResume ? 'Saving...' : 'Save Resume'}
              disabled={savingResume || !resumeText.trim()}
              onAction={handleSaveResume}
            />
            <SourceCard
              title="LinkedIn"
              description="Paste your LinkedIn profile text (About, Experience, Education, Skills)."
              icon={<LinkSimple className="h-4 w-4 text-[#0A66C2]" />}
              value={linkedinText}
              onChange={setLinkedinText}
              placeholder={'Paste your LinkedIn profile text here...'}
              actionLabel={savingLinkedin ? 'Saving...' : 'Save Profile'}
              disabled={savingLinkedin || !linkedinText.trim()}
              onAction={handleSaveLinkedin}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <GitBranch className="h-4 w-4 text-amber-500" /> GitHub (optional)
              </CardTitle>
              <CardDescription>Connect your GitHub username. Available in a future phase.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex max-w-md flex-col gap-2">
                <Label htmlFor="github-username">GitHub username</Label>
                <Input id="github-username" value={githubUsername} onChange={(e) => setGithubUsername(e.target.value)} placeholder="octocat" />
                <p className="text-xs text-muted-foreground">GitHub import is not yet available — this field is a placeholder.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-primary/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkle className="h-4 w-4 text-primary" /> Analyze Profile
              </CardTitle>
              <CardDescription>
                Run AI extraction over your imported sources, merge them into a canonical profile and snapshot a new version.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Button onClick={handleAnalyze} disabled={isAnalyzing} className="w-fit gap-2">
                <Sparkle className="h-4 w-4" />
                {isAnalyzing ? 'Queuing analysis...' : 'Analyze Profile'}
              </Button>
              {lastError && <p className="text-sm text-destructive">{lastError}</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="review" className="space-y-4">
          <ProfileReview
            profile={profileQuery.data ?? null}
            isLoading={profileQuery.isLoading}
            isError={profileQuery.isError}
            isAnalyzing={isAnalyzing}
            hasProfile={hasProfile}
            onRefresh={refreshProfile}
            onAnalyze={handleAnalyze}
          />

          <div className="grid gap-4 lg:grid-cols-2">
            <SourcesCard sources={sources} />
            <VersionsCard versions={versions} />
          </div>

          <SkillCloud skills={skills} />
          <ExperienceList experiences={experiences} />
          <ProjectList projects={projects} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message
  return String(err)
}

function SourceCard({
  title,
  description,
  icon,
  value,
  onChange,
  placeholder,
  actionLabel,
  disabled,
  onAction,
}: {
  title: string
  description: string
  icon: React.ReactNode
  value: string
  onChange: (v: string) => void
  placeholder: string
  actionLabel: string
  disabled: boolean
  onAction: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">{icon} {title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="h-[180px] font-mono text-xs resize-none" />
        <Button variant="outline" className="w-fit gap-1.5" onClick={onAction} disabled={disabled}>
          <Upload className="h-3.5 w-3.5" /> {actionLabel}
        </Button>
      </CardContent>
    </Card>
  )
}

function ProfileReview({
  profile,
  isLoading,
  isError,
  isAnalyzing,
  hasProfile,
  onRefresh,
  onAnalyze,
}: {
  profile: CandidateProfile | null
  isLoading: boolean
  isError: boolean
  isAnalyzing: boolean
  hasProfile: boolean
  onRefresh: () => void
  onAnalyze: () => void
}) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">Loading profile...</CardContent>
      </Card>
    )
  }
  if (isError) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-3 p-6">
          <p className="text-sm text-destructive">Could not load the candidate profile.</p>
          <Button variant="outline" size="sm" className="w-fit" onClick={onRefresh}>Retry</Button>
        </CardContent>
      </Card>
    )
  }
  if (!hasProfile || !profile) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-3 p-6">
          <p className="text-sm text-muted-foreground">
            No profile yet. Add your resume / LinkedIn sources and run <span className="font-medium">Analyze Profile</span>.
          </p>
          <Button size="sm" className="w-fit gap-2" onClick={onAnalyze} disabled={isAnalyzing}>
            <Sparkle className="h-3.5 w-3.5" /> {isAnalyzing ? 'Queuing analysis...' : 'Analyze Profile'}
          </Button>
        </CardContent>
      </Card>
    )
  }
  return (
    <Card className="border-primary/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <CheckCircle className="h-4 w-4 text-primary" /> Profile Summary
        </CardTitle>
        <CardDescription>
          {profile.name || 'Unnamed'} · {profile.title || 'no title'} · profile version {profile.version ?? 1}
          {profile.location ? ` · ${profile.location}` : ''}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {profile.headline && <p className="text-sm text-muted-foreground">{profile.headline}</p>}
        {profile.summary && <p className="text-sm">{profile.summary}</p>}
        <div className="flex flex-wrap gap-2 pt-1">
          <Badge variant="secondary">{profile.skills.length} skills</Badge>
          <Badge variant="secondary">{profile.experiences.length} experiences</Badge>
          <Badge variant="secondary">{profile.projects.length} projects</Badge>
          <Badge variant="secondary">{profile.educations.length} educations</Badge>
          <Badge variant="secondary">{profile.languages.length} languages</Badge>
        </div>
      </CardContent>
    </Card>
  )
}

function SourcesCard({ sources }: { sources: CandidateSource[] }) {
  if (sources.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-base">Connected Sources</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">No sources imported yet.</CardContent>
      </Card>
    )
  }
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Connected Sources</CardTitle></CardHeader>
      <CardContent>
        <ScrollArea className="h-[220px]">
          <ul className="space-y-2">
            {sources.map((s) => (
              <li key={s.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="capitalize">{s.source_type} v{s.version}</span>
                <Badge variant={s.status === 'processed' ? 'default' : 'secondary'}>{s.status}</Badge>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

function VersionsCard({ versions }: { versions: CandidateVersion[] }) {
  if (versions.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-base">Version History</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">No profile versions yet.</CardContent>
      </Card>
    )
  }
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Version History</CardTitle></CardHeader>
      <CardContent>
        <ScrollArea className="h-[220px]">
          <ul className="space-y-2">
            {versions.map((v) => (
              <li key={v.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="font-medium">v{v.version}</span>
                <span className="truncate text-muted-foreground">{v.change_summary || (v.created_at ? new Date(v.created_at).toLocaleString() : '')}</span>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

function SkillCloud({ skills }: { skills: { id: string; name: string; level: number | null; confidence: number | null; evidence: Record<string, unknown> | null }[] }) {
  if (skills.length === 0) return null
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Skills</CardTitle></CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {skills.map((s) => (
          <Badge key={s.id} variant="outline" className="gap-1.5">
            {s.name}
            {s.level != null && <span className="text-muted-foreground">L{s.level}</span>}
            {s.confidence != null && <span className="text-muted-foreground">{(s.confidence * 100).toFixed(0)}%</span>}
          </Badge>
        ))}
      </CardContent>
    </Card>
  )
}

function ExperienceList({ experiences }: { experiences: { id: string; company: string; role: string; start_date: string | null; end_date: string | null; summary: string | null }[] }) {
  if (experiences.length === 0) return null
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Experience</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {experiences.map((e) => (
          <div key={e.id} className="space-y-1">
            <div className="flex items-baseline justify-between gap-2 text-sm">
              <span className="font-medium">{e.role}</span>
              <span className="text-xs text-muted-foreground">{e.company}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {[e.start_date, e.end_date].filter(Boolean).join(' → ') || '—'}
            </div>
            {e.summary && <p className="text-sm text-muted-foreground">{e.summary}</p>}
            <Separator className="my-2" />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function ProjectList({ projects }: { projects: { id: string; name: string; description: string | null; url: string | null }[] }) {
  if (projects.length === 0) return null
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Projects</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {projects.map((p) => (
          <div key={p.id} className="space-y-1">
            <div className="text-sm font-medium">{p.name}</div>
            {p.description && <p className="text-sm text-muted-foreground">{p.description}</p>}
            {p.url && <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">{p.url}</a>}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
