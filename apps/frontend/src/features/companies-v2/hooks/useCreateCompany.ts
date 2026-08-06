'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { companyApi } from '@/entities/company/api'

const COMPANIES_KEY = 'companies-v2-infinite'

export interface CreateCompanyLinkItem {
  url: string
  title: string
}

export interface CreateCompanyNoteItem {
  content: string
}

export interface CreateCompanyRequest {
  name?: string
  notes?: CreateCompanyNoteItem[]
  links?: CreateCompanyLinkItem[]
  source?: string
  queue?: boolean
}

export function useCreateCompany() {
  const queryClient = useQueryClient()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (data: CreateCompanyRequest) => companyApi.create({
      name: data.name || undefined,
      notes: data.notes as unknown as Array<Record<string, unknown>>,
      links: data.links as unknown as Array<Record<string, unknown>>,
      source: data.source ?? 'web',
      queue: data.queue,
    }),
    onError: (e: unknown) => {
      setError((e as { message?: string })?.message || 'Failed to add company')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
    },
  })

  const createCompany = async (data: CreateCompanyRequest): Promise<boolean> => {
    setSubmitting(true)
    setError(null)
    try {
      await mutation.mutateAsync(data)
      return true
    } catch {
      return false
    } finally {
      setSubmitting(false)
    }
  }

  const clearError = () => setError(null)

  return { createCompany, submitting, error, clearError }
}
