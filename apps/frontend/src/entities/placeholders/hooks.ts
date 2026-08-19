'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { placeholdersApi } from './api'
import type { PlaceholderValues } from './types'

const PLACEHOLDERS_KEY = 'placeholders'

export function usePlaceholders() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: [PLACEHOLDERS_KEY],
    queryFn: () => placeholdersApi.list(),
    staleTime: 30_000,
  })

  const updateMutation = useMutation({
    mutationFn: (values: PlaceholderValues) => placeholdersApi.update(values),
    onSettled: () => queryClient.invalidateQueries({ queryKey: [PLACEHOLDERS_KEY] }),
  })

  return { data: query.data, isLoading: query.isLoading, updateMutation }
}

export function usePlaceholderUpdateForm(initial: PlaceholderValues) {
  const [values, setValues] = useState<PlaceholderValues>(initial)

  const setValue = (key: string, value: string) =>
    setValues((prev) => ({ ...prev, [key]: value }))

  return { values, setValue, setValues }
}