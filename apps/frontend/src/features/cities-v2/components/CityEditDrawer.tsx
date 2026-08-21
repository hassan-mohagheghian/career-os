'use client'

import { useState } from 'react'
import { Drawer, DrawerHeader, DrawerContent } from '@/shared/components/Drawer'
import { Input } from '@/shared/ui/input'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { MapPin, Warning, CircleNotch, Plus, X, GitMerge, Crown } from '@phosphor-icons/react'
import {
  useAddCityAlias,
  useRemoveCityAlias,
  usePromoteCityCanonical,
  useMergeCities,
} from '@/entities/city/hooks'
import type { CityListItem } from '@/entities/city/types'
import { formatCityLocation } from '@/shared/lib/formatLocation'
import { MergeCityDialog } from './MergeCityDialog'

function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1">
      <label className="flex items-center gap-0.5 text-xs text-muted-foreground">
        {label}
      </label>
      {hint && <p className="text-2xs text-muted-foreground">{hint}</p>}
      {children}
    </div>
  )
}

interface CityEditDrawerProps {
  city: CityListItem | null
  onOpenChange: (city: CityListItem | null) => void
}

export function CityEditDrawer({ city, onOpenChange }: CityEditDrawerProps) {
  const [name, setName] = useState(city?.city ?? '')
  const [aliases, setAliases] = useState<string[]>(city?.aliases ?? [])
  const [newAlias, setNewAlias] = useState('')
  const [canonicalAlias, setCanonicalAlias] = useState<string | null>(null)
  const [aliasBusy, setAliasBusy] = useState(false)
  const [canonicalPending, setCanonicalPending] = useState(false)
  const [mergeOpen, setMergeOpen] = useState(false)
  const [mergePending, setMergePending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addAliasMutation = useAddCityAlias()
  const removeAliasMutation = useRemoveCityAlias()
  const promoteMutation = usePromoteCityCanonical()
  const mergeMutation = useMergeCities()

  const cityId = city?.id ?? null

  const handleAddAlias = async () => {
    if (!cityId) return
    const alias = newAlias.trim()
    if (!alias || aliases.includes(alias)) return
    setAliasBusy(true)
    setError(null)
    try {
      const updated = await addAliasMutation.mutateAsync({ cityId, aliasName: alias })
      setAliases(updated.aliases ?? [...aliases, alias])
      setNewAlias('')
    } catch {
      setError('Failed to add alias.')
    } finally {
      setAliasBusy(false)
    }
  }

  const handleRemoveAlias = async (alias: string) => {
    if (!cityId) return
    setAliasBusy(true)
    setError(null)
    try {
      const updated = await removeAliasMutation.mutateAsync({ cityId, aliasName: alias })
      setAliases(updated.aliases ?? aliases.filter((a) => a !== alias))
    } catch {
      setError('Failed to remove alias.')
    } finally {
      setAliasBusy(false)
    }
  }

  const handlePromoteAlias = async () => {
    if (!cityId || canonicalAlias == null) return
    setCanonicalPending(true)
    setError(null)
    try {
      const updated = await promoteMutation.mutateAsync({ cityId, aliasName: canonicalAlias })
      setName(updated.city ?? canonicalAlias)
      setAliases(updated.aliases ?? [])
      setCanonicalAlias(null)
    } catch {
      setError('Failed to promote alias. Make sure it does not clash with another city.')
    } finally {
      setCanonicalPending(false)
    }
  }

  const handleMerge = async (targetId: string) => {
    if (!cityId) return
    setMergePending(true)
    setError(null)
    try {
      await mergeMutation.mutateAsync({ targetId, sourceIds: [cityId] })
      onOpenChange(null)
    } catch {
      setError('Failed to merge city.')
    } finally {
      setMergePending(false)
    }
  }

  const canonicalLabel = name && city?.country
    ? formatCityLocation(name, city.country)
    : name || 'this city'

  return (
    <Drawer
      open={city != null}
      onOpenChange={(o) => {
        if (!o) onOpenChange(null)
      }}
    >
      <DrawerHeader
        title={
          <span className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" /> Edit City
          </span>
        }
        onClose={() => onOpenChange(null)}
      />
      <DrawerContent>
        {error && (
          <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
            <Warning className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        {city != null && (
          <div className="space-y-3">
            <Field label="City" hint="The canonical city name">
              <Input value={name} onChange={(e) => setName(e.target.value)} disabled />
            </Field>
            <Field label="Country">
              <Input value={city.country} disabled />
            </Field>

            <Field
              label="Aliases"
              hint="Other names for this city (e.g. 'München' for 'Munich')"
            >
              <div className="space-y-2">
                {aliases.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {aliases.map((a) => (
                      <Badge key={a} variant="outline" className="gap-1 pr-1 text-2xs">
                        {a}
                        <button
                          type="button"
                          onClick={() => handleRemoveAlias(a)}
                          className="rounded-full p-0.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                          aria-label={`Remove alias ${a}`}
                          disabled={aliasBusy}
                        >
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-2xs text-muted-foreground">No aliases yet.</p>
                )}
                <div className="flex items-center gap-1">
                  <Input
                    value={newAlias}
                    onChange={(e) => setNewAlias(e.target.value)}
                    placeholder="Add alias..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddAlias()
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    className="h-7 w-7 shrink-0"
                    onClick={handleAddAlias}
                    disabled={aliasBusy || !newAlias.trim()}
                    aria-label="Add alias"
                  >
                    {aliasBusy ? (
                      <CircleNotch className="w-3 h-3 animate-spin" />
                    ) : (
                      <Plus className="w-3 h-3" />
                    )}
                  </Button>
                </div>
                {aliases.length > 0 && (
                  <div className="pt-1 border-t border-border/40">
                    <label className="text-2xs text-muted-foreground mb-1 block">
                      Make an alias the canonical name
                    </label>
                    <div className="flex items-center gap-1">
                      <select
                        value={canonicalAlias ?? ''}
                        onChange={(e) => setCanonicalAlias(e.target.value || null)}
                        className="h-7 flex-1 rounded-md border border-input bg-transparent px-2 text-xs"
                        aria-label="Alias to promote to canonical"
                      >
                        <option value="">Choose alias...</option>
                        {aliases.map((a) => (
                          <option key={a} value={a}>
                            {a}
                          </option>
                        ))}
                      </select>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="h-7 gap-1 text-2xs shrink-0"
                        onClick={handlePromoteAlias}
                        disabled={canonicalAlias == null || canonicalPending}
                      >
                        {canonicalPending ? (
                          <CircleNotch className="w-3 h-3 animate-spin" />
                        ) : (
                          <Crown className="w-3 h-3" />
                        )}
                        Make canonical
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </Field>

            <div className="pt-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-2xs gap-1"
                onClick={() => setMergeOpen(true)}
              >
                <GitMerge className="w-3 h-3" /> Merge into another city
              </Button>
            </div>
          </div>
        )}
      </DrawerContent>

      <MergeCityDialog
        sources={city ? [{ id: city.id, name: canonicalLabel }] : []}
        open={mergeOpen}
        onOpenChange={setMergeOpen}
        onMerge={handleMerge}
        pending={mergePending}
      />
    </Drawer>
  )
}