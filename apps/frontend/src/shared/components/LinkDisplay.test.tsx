import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import LinkDisplay, { truncateLink, normalizeLinkUrl, isSafeLink } from './LinkDisplay'
import { TooltipProvider } from '@/shared/ui/tooltip'

function renderLink(props: Partial<Parameters<typeof LinkDisplay>[0]> = {}) {
  const base = { url: 'https://example.com/jobs/123' }
  return render(
    <TooltipProvider delayDuration={0}>
      <LinkDisplay {...base} {...props} />
    </TooltipProvider>
  )
}

describe('truncateLink', () => {
  it('keeps short URLs intact', () => {
    expect(truncateLink('https://example.com/job')).toBe('example.com/job')
  })

  it('truncates long URLs with an ellipsis', () => {
    const long = 'https://www.linkedin.com/jobs/view/12345678901234567890'
    const out = truncateLink(long, 25)
    expect(out.endsWith('...')).toBe(true)
    expect(out.length).toBe(28)
    expect(out.startsWith('linkedin.com')).toBe(true)
  })

  it('strips protocol and www for display', () => {
    expect(truncateLink('https://www.acme.example.com', 100)).toBe('acme.example.com')
  })
})

describe('normalizeLinkUrl', () => {
  it('adds https:// when scheme is missing', () => {
    expect(normalizeLinkUrl('acme.example.com/jobs')).toBe('https://acme.example.com/jobs')
  })

  it('keeps existing http(s) and mailto schemes', () => {
    expect(normalizeLinkUrl('http://example.com')).toBe('http://example.com')
    expect(normalizeLinkUrl('mailto:hr@example.com')).toBe('mailto:hr@example.com')
  })
})

describe('isSafeLink', () => {
  it('rejects unsafe schemes', () => {
    expect(isSafeLink('javascript:alert(1)')).toBe(false)
    expect(isSafeLink('data:text/html,hi')).toBe(false)
  })

  it('accepts http(s) and mailto', () => {
    expect(isSafeLink('https://example.com')).toBe(true)
    expect(isSafeLink('mailto:a@b.com')).toBe(true)
  })
})

describe('LinkDisplay', () => {
  it('renders the truncated URL when no title is provided', () => {
    renderLink()
    expect(screen.getByText('example.com/jobs/123')).toBeInTheDocument()
  })

  it('renders the title when provided', () => {
    renderLink({ title: 'Company Careers', url: 'https://example.com/very/long/careers/page/with/more/path' })
    expect(screen.getByText('Company Careers')).toBeInTheDocument()
  })

  it('opens the link in a new tab with safe rel attributes', () => {
    renderLink()
    const link = screen.getByRole('link', { name: 'Open link' })
    expect(link).toHaveAttribute('href', 'https://example.com/jobs/123')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('does not render a clickable anchor for unsafe schemes', () => {
    renderLink({ url: 'javascript:alert(1)' })
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('copies the URL to the clipboard and shows the copied state', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    renderLink({ url: 'https://example.com/jobs/123' })
    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }))
    expect(writeText).toHaveBeenCalledWith('https://example.com/jobs/123')
    expect(await screen.findByRole('button', { name: 'Copied' })).toBeInTheDocument()
  })

  it('shows the full URL in the tooltip', async () => {
    const user = userEvent.setup()
    const longUrl = 'https://www.linkedin.com/jobs/view/123456789012345678901234567890'
    renderLink({ url: longUrl })
    await user.hover(screen.getByRole('link', { name: 'Open link' }))
    expect(await screen.findByText(longUrl)).toBeInTheDocument()
  })
})
