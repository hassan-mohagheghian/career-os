import type { Meta, StoryObj } from '@storybook/react'
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './dialog'
import { Button } from './button'

const meta: Meta<typeof Dialog> = {
  title: 'shared/ui/Dialog',
  component: Dialog,
  tags: ['autodocs'],
  render: () => (
    <Dialog open>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when you are done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <label className="text-right text-sm">Name</label>
            <input className="col-span-3 flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm" defaultValue="John Doe" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <label className="text-right text-sm">Email</label>
            <input className="col-span-3 flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm" defaultValue="john@example.com" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
}

export default meta
type Story = StoryObj<typeof Dialog>

export const Default: Story = {}

export const SimpleDialog: Story = {
  render: () => (
    <Dialog open>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm</DialogTitle>
          <DialogDescription>
            Are you sure you want to proceed with this action?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
}
