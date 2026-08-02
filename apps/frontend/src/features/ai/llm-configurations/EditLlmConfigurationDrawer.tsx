import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Checkbox } from '@/shared/ui/checkbox'
import { Drawer, DrawerHeader, DrawerContent, DrawerFooter } from '@/shared/components/Drawer'
import { llmConfigurationApi } from '@/entities/llm-configuration/api'
import type { LLMConfiguration } from '@/entities/llm-configuration/types'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: LLMConfiguration
  onSaved: () => void
}

export default function EditLlmConfigurationDrawer({ open, onOpenChange, config, onSaved }: Props) {
  const [name, setName] = useState(config.name)
  const [model, setModel] = useState(config.model)
  const [modelVersion, setModelVersion] = useState(config.model_version || '')
  const [enabled, setEnabled] = useState(config.enabled)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    setName(config.name)
    setModel(config.model)
    setModelVersion(config.model_version || '')
    setEnabled(config.enabled)
    setErrors({})
  }, [config])

  const handleSubmit = async () => {
    const newErrors: Record<string, string> = {}
    if (!name.trim()) newErrors.name = 'Name is required'
    if (!model.trim()) newErrors.model = 'Model is required'
    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return

    setSubmitting(true)
    try {
      await llmConfigurationApi.update(config.id, {
        name: name.trim(),
        model: model.trim(),
        model_version: modelVersion.trim() || null,
        enabled,
      })
      toast.success('Configuration updated')
      onOpenChange(false)
      onSaved()
    } catch (e: any) {
      toast.error(e.message || 'Failed to update configuration')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerHeader title="Edit LLM Configuration" onClose={() => onOpenChange(false)} />
      <DrawerContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Name *</Label>
            <Input id="edit-name" value={name} onChange={e => setName(e.target.value)} />
            {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
          </div>

          <div className="space-y-2">
            <Label>Executor</Label>
            <div className="text-sm text-muted-foreground bg-muted px-3 py-2 rounded-md">OpenCode</div>
          </div>

          <div className="space-y-2">
            <Label>Provider</Label>
            <div className="text-sm text-muted-foreground bg-muted px-3 py-2 rounded-md">OpenAI</div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-model">Model *</Label>
            <Input id="edit-model" value={model} onChange={e => setModel(e.target.value)} />
            {errors.model && <p className="text-sm text-destructive">{errors.model}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-modelVersion">Model Version</Label>
            <Input id="edit-modelVersion" value={modelVersion} onChange={e => setModelVersion(e.target.value)} />
          </div>

          <div className="flex items-center gap-2">
            <Checkbox id="edit-enabled" checked={enabled} onCheckedChange={(v) => setEnabled(v === true)} />
            <Label htmlFor="edit-enabled" className="cursor-pointer">Enabled</Label>
          </div>
        </div>
      </DrawerContent>
      <DrawerFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
        <Button onClick={handleSubmit} disabled={submitting}>Save</Button>
      </DrawerFooter>
    </Drawer>
  )
}
