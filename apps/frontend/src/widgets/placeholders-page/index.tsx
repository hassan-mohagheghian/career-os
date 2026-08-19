'use client'

import { useState } from 'react'
import { Check } from '@phosphor-icons/react'
import { toast } from 'sonner'
import MainLayout from '@/widgets/main-layout'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { usePlaceholders } from '@/entities/placeholders/hooks'

function PlaceholdersForm() {
  const { data, isLoading, updateMutation } = usePlaceholders()
  const [values, setValues] = useState<Record<string, string>>({})

  if (isLoading) {
    return <div className="text-muted-foreground text-sm p-6">Loading placeholders…</div>
  }

  const keys = data?.keys ?? []
  const current = (key: string) => values[key] ?? data?.values?.[key] ?? ''

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = () => {
    updateMutation.mutate(values, {
      onSuccess: () => {
        toast.success('Placeholders saved')
        setValues({})
      },
      onError: () => {
        toast.error('Failed to save placeholders')
      },
    })
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Placeholders</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Personal details injected into generated resumes and cover letters. Fill these once
          and use the Download PDF action on a generated document.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your details</CardTitle>
          <CardDescription>
            These values replace the {'{{name}}'} tokens in generated documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {keys.map(({ key, label }) => (
            <div key={key} className="grid gap-1.5">
              <Label htmlFor={`ph-${key}`} className="text-xs">
                {label}
              </Label>
              <Input
                id={`ph-${key}`}
                value={current(key)}
                onChange={(e) => handleChange(key, e.target.value)}
                placeholder={label}
                className="h-9 text-sm"
              />
            </div>
          ))}
          <div className="flex justify-end pt-2">
            <Button size="sm" onClick={handleSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving…' : <Check className="w-4 h-4 mr-1" />}
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function PlaceholdersPageWidget() {
  return (
    <MainLayout>
      <PlaceholdersForm />
    </MainLayout>
  )
}