import { useState } from 'react'
import { Check, X } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { Drawer, DrawerHeader, DrawerContent, DrawerFooter } from '@/shared/components/Drawer'

interface RuleFormValues {
  category: string
  scope: string
  key: string
  value: string
  description: string
  priority: number
}

interface RuleFormDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  initial: RuleFormValues
  onSave: (form: RuleFormValues) => void
}

const DEFAULT_RULE: RuleFormValues = {
  category: 'fit',
  scope: 'JOB',
  key: '',
  value: '',
  description: '',
  priority: 50,
}

export default function RuleFormDrawer({ open, onOpenChange, title, initial, onSave }: RuleFormDrawerProps) {
  const [f, setF] = useState<RuleFormValues>(initial || DEFAULT_RULE)

  return (
    <Drawer open={open} onOpenChange={onOpenChange} placement="bottom" variant="full">
      <DrawerHeader title={title} onClose={() => onOpenChange(false)} />
      <DrawerContent>
        <div className="mx-auto w-full max-w-[560px] space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Scope</Label>
              <Select value={f.scope} onValueChange={(v) => setF({ ...f, scope: v })}>
                <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="SHARED">Shared (ALL)</SelectItem>
                  <SelectItem value="JOB">Job</SelectItem>
                  <SelectItem value="COMPANY_PRODUCT">Product Company</SelectItem>
                  <SelectItem value="COMPANY_RECRUITING">Recruiting</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <Select value={f.category} onValueChange={(v) => setF({ ...f, category: v })}>
                <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="fit">Fit score</SelectItem>
                  <SelectItem value="success">Success score</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Key name</Label>
              <Input value={f.key} onChange={e => setF({ ...f, key: e.target.value })} placeholder="e.g. remote_work" className="h-8 text-xs" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Priority (0-100)</Label>
              <Input type="number" min="0" max="100" value={f.priority} onChange={e => setF({ ...f, priority: parseInt(e.target.value) || 0 })} className="h-8 text-xs" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Value / rule</Label>
            <Textarea value={f.value} onChange={e => setF({ ...f, value: e.target.value })} placeholder="How the rule matches candidates / companies" className="text-xs min-h-[72px]" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">How this affects scoring (optional)</Label>
            <Input value={f.description} onChange={e => setF({ ...f, description: e.target.value })} placeholder="Optional description" className="h-8 text-xs" />
          </div>
        </div>
      </DrawerContent>
      <DrawerFooter>
        <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}><X className="w-3 h-3" /> Cancel</Button>
        <Button size="sm" className="bg-green-500 hover:bg-green-600" disabled={!f.key || !f.value} onClick={() => { if (f.key && f.value) onSave(f) }}><Check className="w-3 h-3" /> Save</Button>
      </DrawerFooter>
    </Drawer>
  )
}
