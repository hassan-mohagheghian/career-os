import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import SkillsIntelSection from '@/features/insights/components/SkillsIntelSection'
import { useSkills } from '../hooks/useSkills'

export default function SkillsTab() {
  const {
    skillRoadmapProgress, skillGenJobs,
    refreshSkillRoadmapProgress,
  } = useSkills()

  const activeJobs = skillGenJobs.filter((j: any) => j.status === 'running' || j.status === 'queued')

  return (
    <div className="space-y-5">
      {/* Active Generation Jobs */}
      {activeJobs.length > 0 && (
        <div className="space-y-1">
          {activeJobs.map((job: any) => (
            <GenerationProgressCard
              key={job.skill}
              title={job.skill}
              progress={{ running: true, ...job }}
              compact
            />
          ))}
        </div>
      )}

      {/* Full Skills Management — no AI insights data, just tech_stack + roadmaps */}
      <SkillsIntelSection
        data={{}}
        refreshing={{}}
        onRefresh={() => {}}
        roadmapProgress={skillRoadmapProgress}
        onRefreshProgress={refreshSkillRoadmapProgress}
        genJobs={activeJobs}
        status={{}}
      />
    </div>
  )
}
