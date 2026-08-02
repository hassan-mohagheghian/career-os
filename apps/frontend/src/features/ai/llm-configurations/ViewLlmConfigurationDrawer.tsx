import { Button } from '@/shared/ui/button'
import { Drawer, DrawerHeader, DrawerContent, DrawerFooter } from '@/shared/components/Drawer'
import { Field } from '@/shared/components/DrawerComponents'
import { Badge } from '@/shared/ui/badge'
import type { LLMConfiguration } from '@/entities/llm-configuration/types'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: LLMConfiguration
}

export default function ViewLlmConfigurationDrawer({ open, onOpenChange, config }: Props) {
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerHeader title={config.name} onClose={() => onOpenChange(false)} />
      <DrawerContent>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant={config.enabled ? 'default' : 'secondary'}>
              {config.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>

          <Field label="Executor" value={config.executor} />
          <Field label="Provider" value={config.provider} />
          <Field label="Model" value={config.model} />
          <Field label="Model Version" value={config.model_version || '-'} />
          <Field label="Created At" value={config.created_at ? new Date(config.created_at).toLocaleString() : '-'} />
          <Field label="Updated At" value={config.updated_at ? new Date(config.updated_at).toLocaleString() : '-'} />
        </div>
      </DrawerContent>
      <DrawerFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
      </DrawerFooter>
    </Drawer>
  )
}
