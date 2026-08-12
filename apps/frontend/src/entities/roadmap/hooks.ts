'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { roadmapApi } from './api'
import type {
  CreateMilestoneInput,
  CreateNoteInput,
  CreateResourceInput,
  CreateRoadmapInput,
  CreateTaskInput,
  UpdateMilestoneInput,
  UpdateResourceInput,
  UpdateRoadmapInput,
  UpdateTaskInput,
} from './types'

const ROADMAP_KEY = 'roadmap'

export function useRoadmapsQuery() {
  return useQuery({
    queryKey: [ROADMAP_KEY, 'list'],
    queryFn: () => roadmapApi.list(),
  })
}

export function useRoadmapQuery(roadmapId: string | null) {
  return useQuery({
    queryKey: [ROADMAP_KEY, roadmapId],
    queryFn: () => roadmapApi.get(roadmapId!),
    enabled: !!roadmapId,
  })
}

export function useRoadmapByApplicationQuery(applicationId: string | null) {
  return useQuery({
    queryKey: [ROADMAP_KEY, 'by-application', applicationId],
    queryFn: () => roadmapApi.getByApplication(applicationId!),
    enabled: !!applicationId,
  })
}

function useRoadmapInvalidations() {
  const queryClient = useQueryClient()
  return {
    invalidate: (roadmapId?: string) => {
      queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY, 'list'] })
      if (roadmapId) queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY, roadmapId] })
      queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY, 'by-application'] })
    },
  }
}

export function useCreateRoadmapMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (input: CreateRoadmapInput) => roadmapApi.create(input),
    onSettled: () => invalidate(),
  })
}

export function useUpdateRoadmapMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ roadmapId, input }: { roadmapId: string; input: UpdateRoadmapInput }) =>
      roadmapApi.update(roadmapId, input),
    onSettled: (_data, _error, vars) => invalidate(vars.roadmapId),
  })
}

export function useDeleteRoadmapMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (roadmapId: string) => roadmapApi.remove(roadmapId),
    onSettled: () => invalidate(),
  })
}

export function useAddMilestoneMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ roadmapId, input }: { roadmapId: string; input: CreateMilestoneInput }) =>
      roadmapApi.addMilestone(roadmapId, input),
    onSettled: (_data, _error, vars) => invalidate(vars.roadmapId),
  })
}

export function useUpdateMilestoneMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ milestoneId, input }: { milestoneId: string; input: UpdateMilestoneInput }) =>
      roadmapApi.updateMilestone(milestoneId, input),
    onSettled: (_data, _error, vars) => invalidate(),
  })
}

export function useDeleteMilestoneMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (milestoneId: string) => roadmapApi.removeMilestone(milestoneId),
    onSettled: () => invalidate(),
  })
}

export function useAddTaskMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ milestoneId, input }: { milestoneId: string; input: CreateTaskInput }) =>
      roadmapApi.addTask(milestoneId, input),
    onSettled: () => invalidate(),
  })
}

export function useUpdateTaskMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ taskId, input }: { taskId: string; input: UpdateTaskInput }) =>
      roadmapApi.updateTask(taskId, input),
    onSettled: () => invalidate(),
  })
}

export function useDeleteTaskMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (taskId: string) => roadmapApi.removeTask(taskId),
    onSettled: () => invalidate(),
  })
}

export function useAddNoteMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ roadmapId, input }: { roadmapId: string; input: CreateNoteInput }) =>
      roadmapApi.addNote(roadmapId, input),
    onSettled: () => invalidate(),
  })
}

export function useDeleteNoteMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (noteId: string) => roadmapApi.removeNote(noteId),
    onSettled: () => invalidate(),
  })
}

export function useAddResourceMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ roadmapId, input }: { roadmapId: string; input: CreateResourceInput }) =>
      roadmapApi.addResource(roadmapId, input),
    onSettled: () => invalidate(),
  })
}

export function useUpdateResourceMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: ({ resourceId, input }: { resourceId: string; input: UpdateResourceInput }) =>
      roadmapApi.updateResource(resourceId, input),
    onSettled: () => invalidate(),
  })
}

export function useDeleteResourceMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (resourceId: string) => roadmapApi.removeResource(resourceId),
    onSettled: () => invalidate(),
  })
}

export function useLinkSkillMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (input: { skill_name: string; milestone_id?: string | null; task_id?: string | null }) =>
      roadmapApi.linkSkill(input),
    onSettled: () => invalidate(),
  })
}

export function useRemoveSkillLinkMutation() {
  const { invalidate } = useRoadmapInvalidations()
  return useMutation({
    mutationFn: (linkId: string) => roadmapApi.removeSkillLink(linkId),
    onSettled: () => invalidate(),
  })
}