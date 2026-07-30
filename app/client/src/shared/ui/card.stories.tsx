import type { Meta, StoryObj } from '@storybook/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card'

const meta: Meta<typeof Card> = {
  title: 'shared/ui/Card',
  component: Card,
  tags: ['autodocs'],
  render: (args) => (
    <Card {...args}>
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here.</p>
      </CardContent>
      <CardFooter>
        <p>Card footer</p>
      </CardFooter>
    </Card>
  ),
}

export default meta
type Story = StoryObj<typeof Card>

export const Default: Story = {}

export const OnlyHeader: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Header Only</CardTitle>
        <CardDescription>Just the header section</CardDescription>
      </CardHeader>
    </Card>
  ),
}

export const WithLongContent: Story = {
  render: () => (
    <Card className="max-w-sm">
      <CardHeader>
        <CardTitle>Job Position</CardTitle>
        <CardDescription>Senior Software Engineer</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Berlin, Germany • Full-time • Visa sponsored</p>
        <p className="mt-2 text-sm text-muted-foreground">
          We are looking for an experienced software engineer to join our platform team.
        </p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <span className="text-sm text-muted-foreground">Posted 2 days ago</span>
        <span className="text-sm font-medium">Match: 85%</span>
      </CardFooter>
    </Card>
  ),
}
