import { api } from '@/shared/api'
import type {
  CreateMilestoneInput,
  CreateNoteInput,
  CreateResourceInput,
  CreateRoadmapInput,
  CreateTaskInput,
  DeleteResponse,
  RoadmapDetail,
  RoadmapMilestone,
  RoadmapNote,
  RoadmapResource,
  RoadmapSkillLink,
  RoadmapSummary,
  RoadmapTask,
  UpdateMilestoneInput,
  UpdateResourceInput,
  UpdateRoadmapInput,
  UpdateTaskInput,
} from './types'

export const roadmapApi = {
  list: () => api.get<RoadmapSummary[]>('/roadmaps'),
  get: (roadmapId: string) => api.get<RoadmapDetail>(`/roadmaps/${roadmapId}`),
  getByApplication: (applicationId: string) =>
    api.get<RoadmapDetail>(`/roadmaps/by-application/${applicationId}`),
  create: (input: CreateRoadmapInput) => api.post<RoadmapDetail>('/roadmaps', input),
  update: (roadmapId: string, input: UpdateRoadmapInput) =>
    api.patch<RoadmapDetail>(`/roadmaps/${roadmapId}`, input),
  remove: (roadmapId: string) => api.delete<DeleteResponse>(`/roadmaps/${roadmapId}`),

  addMilestone: (roadmapId: string, input: CreateMilestoneInput) =>
    api.post<RoadmapMilestone>(`/roadmaps/${roadmapId}/milestones`, input),
  updateMilestone: (milestoneId: string, input: UpdateMilestoneInput) =>
    api.patch<RoadmapMilestone>(`/roadmaps/milestones/${milestoneId}`, input),
  removeMilestone: (milestoneId: string) =>
    api.delete<DeleteResponse>(`/roadmaps/milestones/${milestoneId}`),

  addTask: (milestoneId: string, input: CreateTaskInput) =>
    api.post<RoadmapTask>(`/roadmaps/milestones/${milestoneId}/tasks`, input),
  updateTask: (taskId: string, input: UpdateTaskInput) =>
    api.patch<RoadmapTask>(`/roadmaps/tasks/${taskId}`, input),
  removeTask: (taskId: string) => api.delete<DeleteResponse>(`/roadmaps/tasks/${taskId}`),

  addNote: (roadmapId: string, input: CreateNoteInput) =>
    api.post<RoadmapNote>(`/roadmaps/${roadmapId}/notes`, input),
  removeNote: (noteId: string) => api.delete<DeleteResponse>(`/roadmaps/notes/${noteId}`),

  addResource: (roadmapId: string, input: CreateResourceInput) =>
    api.post<RoadmapResource>(`/roadmaps/${roadmapId}/resources`, input),
  updateResource: (resourceId: string, input: UpdateResourceInput) =>
    api.patch<RoadmapResource>(`/roadmaps/resources/${resourceId}`, input),
  removeResource: (resourceId: string) =>
    api.delete<DeleteResponse>(`/roadmaps/resources/${resourceId}`),

  linkSkill: (input: { skill_name: string; milestone_id?: string | null; task_id?: string | null }) =>
    api.post<RoadmapSkillLink>('/roadmaps/skills', input),
  removeSkillLink: (linkId: string) =>
    api.delete<DeleteResponse>(`/roadmaps/skills/${linkId}`),
}