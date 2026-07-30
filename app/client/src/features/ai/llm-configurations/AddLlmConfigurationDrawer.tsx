import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Checkbox } from '@/shared/ui/checkbox'
import { Drawer, DrawerHeader, DrawerContent, DrawerFooter } from '@/shared/components/Drawer'
import { llmConfigurationApi } from '@/entities/llm-configuration/api'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}

export default function AddLlmConfigurationDrawer({ open, onOpenChange, onSaved }: Props) {
  const [name, setName] = useState('')
  const [model, setModel] = useState('')
  const [modelVersion, setModelVersion] = useState('')
  const [enabled, setEnabled] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const reset = () => {
    setName('')
    setModel('')
    setModelVersion('')
    setEnabled(true)
    setErrors({})
  }

  const handleSubmit = async () => {
    const newErrors: Record<string, string> = {}
    if (!name.trim()) newErrors.name = 'Name is required'
    if (!model.trim()) newErrors.model = 'Model is required'
    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return

    setSubmitting(true)
    try {
      await llmConfigurationApi.create({
        name: name.trim(),
        model: model.trim(),
        model_version: modelVersion.trim() || null,
        enabled,
      })
      toast.success('Configuration created')
      reset()
      onOpenChange(false)
      onSaved()
    } catch (e: any) {
      toast.error(e.message || 'Failed to create configuration')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Drawer open={open} onOpenChange={(v) => { if (!v) reset(); onOpenChange(v) }}>
      <DrawerHeader title="Add LLM Configuration" onClose={() => { reset(); onOpenChange(false) }} />
      <DrawerContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="Production GPT-5" />
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
            <Label htmlFor="model">Model *</Label>
            <Input id="model" value={model} onChange={e => setModel(e.target.value)} placeholder="gpt-5" />
            {errors.model && <p className="text-sm text-destructive">{errors.model}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="modelVersion">Model Version</Label>
            <Input id="modelVersion" value={modelVersion} onChange={e => setModelVersion(e.target.value)} placeholder="2027-01" />
          </div>

          <div className="flex items-center gap-2">
            <Checkbox id="enabled" checked={enabled} onCheckedChange={(v) => setEnabled(v === true)} />
            <Label htmlFor="enabled" className="cursor-pointer">Enabled</Label>
          </div>
        </div>
      </DrawerContent>
      <DrawerFooter>
        <Button variant="outline" onClick={() => { reset(); onOpenChange(false) }}>Cancel</Button>
        <Button onClick={handleSubmit} disabled={submitting}>Create</Button>
      </DrawerFooter>
    </Drawer>
  )
}
