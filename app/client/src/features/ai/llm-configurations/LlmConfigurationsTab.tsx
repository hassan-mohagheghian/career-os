import { useState, useEffect } from 'react'
import { Plus, DotsThreeVertical, Eye, PencilLine, Trash, Play, Stop } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverTrigger, PopoverContent } from '@/shared/ui/popover'
import { Badge } from '@/shared/ui/badge'
import { Card, CardHeader, CardContent } from '@/shared/ui/card'
import { llmConfigurationApi } from '@/entities/llm-configuration/api'
import type { LLMConfiguration } from '@/entities/llm-configuration/types'
import AddLlmConfigurationDrawer from './AddLlmConfigurationDrawer'
import EditLlmConfigurationDrawer from './EditLlmConfigurationDrawer'
import ViewLlmConfigurationDrawer from './ViewLlmConfigurationDrawer'

export default function LlmConfigurationsTab() {
  const [configs, setConfigs] = useState<LLMConfiguration[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<LLMConfiguration | null>(null)
  const [viewTarget, setViewTarget] = useState<LLMConfiguration | null>(null)

  const fetch = async () => {
    setLoading(true)
    setError(false)
    try {
      const data = await llmConfigurationApi.list()
      setConfigs(data)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  const handleDelete = async (config: LLMConfiguration) => {
    try {
      await llmConfigurationApi.delete(config.id)
      toast.success('Configuration deleted')
      fetch()
    } catch (e: any) {
      toast.error(e.message || 'Failed to delete configuration')
    }
  }

  const handleToggle = async (config: LLMConfiguration) => {
    try {
      if (config.enabled) {
        await llmConfigurationApi.disable(config.id)
        toast.success('Configuration disabled')
      } else {
        await llmConfigurationApi.enable(config.id)
        toast.success('Configuration enabled')
      }
      fetch()
    } catch (e: any) {
      toast.error(e.message || 'Failed to update configuration')
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">LLM Configurations</h2>
        </div>
        {[1, 2, 3].map(i => (
          <Card key={i} className="animate-pulse"><CardContent className="h-24" /></Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">LLM Configurations</h2>
        </div>
        <div className="text-center py-12 text-muted-foreground">
          <p className="mb-4">Unable to load configurations.</p>
          <Button variant="outline" onClick={fetch}>Retry</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">LLM Configurations</h2>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="w-4 h-4 mr-1" /> Add Configuration
        </Button>
      </div>

      {!configs || configs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="mb-4">No LLM Configurations found. Create your first configuration.</p>
          <Button onClick={() => setAddOpen(true)}>
            <Plus className="w-4 h-4 mr-1" /> Add Configuration
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map(config => (
            <Card key={config.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{config.name}</span>
                    <Badge variant={config.enabled ? 'default' : 'secondary'}>
                      {config.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground space-y-0.5">
                    <div>Executor: {config.executor}</div>
                    <div>Provider: {config.provider}</div>
                    <div>Model: {config.model}{config.model_version ? ` (${config.model_version})` : ''}</div>
                  </div>
                </div>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="icon" className="shrink-0">
                      <DotsThreeVertical className="w-4 h-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent align="end" className="w-40 p-1">
                    <div className="flex flex-col gap-0.5">
                      <button
                        onClick={() => setViewTarget(config)}
                        className="flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent text-left"
                      >
                        <Eye className="w-4 h-4" /> View
                      </button>
                      <button
                        onClick={() => setEditTarget(config)}
                        className="flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent text-left"
                      >
                        <PencilLine className="w-4 h-4" /> Edit
                      </button>
                      <button
                        onClick={() => handleToggle(config)}
                        className="flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent text-left"
                      >
                        {config.enabled
                          ? <><Stop className="w-4 h-4" /> Disable</>
                          : <><Play className="w-4 h-4" /> Enable</>
                        }
                      </button>
                      <button
                        onClick={() => handleDelete(config)}
                        className="flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent text-left text-destructive"
                      >
                        <Trash className="w-4 h-4" /> Delete
                      </button>
                    </div>
                  </PopoverContent>
                </Popover>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      <AddLlmConfigurationDrawer
        open={addOpen}
        onOpenChange={setAddOpen}
        onSaved={fetch}
      />

      {editTarget && (
        <EditLlmConfigurationDrawer
          open={!!editTarget}
          onOpenChange={(open) => { if (!open) setEditTarget(null) }}
          config={editTarget}
          onSaved={fetch}
        />
      )}

      {viewTarget && (
        <ViewLlmConfigurationDrawer
          open={!!viewTarget}
          onOpenChange={(open) => { if (!open) setViewTarget(null) }}
          config={viewTarget}
        />
      )}
    </div>
  )
}
