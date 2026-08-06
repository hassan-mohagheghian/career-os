import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import CreateEntityDrawer, { type CreateEntityFormData } from './CreateEntityDrawer'

vi.mock('@/shared/ui/sheet', () => ({
  Sheet: ({ children }: any) => <div>{children}</div>,
  SheetContent: ({ children }: any) => <div>{children}</div>,
  SheetHeader: ({ children }: any) => <div>{children}</div>,
  SheetTitle: ({ children }: any) => <div>{children}</div>,
}))

const readClipboardUrlMock = vi.fn()
vi.mock('@/shared/lib/clipboard', () => ({
  readClipboardUrl: (...args: any[]) => readClipboardUrlMock(...args),
}))

beforeEach(() => {
  readClipboardUrlMock.mockReset()
  readClipboardUrlMock.mockResolvedValue(null)
})

function renderDrawer(mode: 'job' | 'company', onSubmit: (data: CreateEntityFormData) => void = vi.fn()) {
  return render(
    <CreateEntityDrawer open onOpenChange={vi.fn()} mode={mode} onSubmit={onSubmit} />
  )
}

describe('CreateEntityDrawer — job mode', () => {
  it('renders the job fields and title', () => {
    renderDrawer('job')
    expect(screen.getByText('Import Job')).toBeInTheDocument()
    expect(screen.getByText('Job Post URL')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Senior Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('Additional Links')).toBeInTheDocument()
    expect(screen.getByText('Notes')).toBeInTheDocument()
  })

  it('disables submit until a valid URL is entered', () => {
    renderDrawer('job')
    const addButton = screen.getByText('Add') as HTMLButtonElement
    const queueButton = screen.getByText('Add & Queue') as HTMLButtonElement
    expect(addButton.disabled).toBe(true)
    expect(queueButton.disabled).toBe(true)
    fireEvent.change(screen.getByPlaceholderText('https://linkedin.com/jobs/view/...'), {
      target: { value: 'https://example.com/job' },
    })
    expect(addButton.disabled).toBe(false)
    expect(queueButton.disabled).toBe(false)
  })

  it('Add submits without queue', () => {
    const onSubmit = vi.fn()
    renderDrawer('job', onSubmit)
    fireEvent.change(screen.getByPlaceholderText('https://linkedin.com/jobs/view/...'), {
      target: { value: 'https://example.com/job' },
    })
    fireEvent.click(screen.getByText('Add'))
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ queue: false, job_post_url: 'https://example.com/job' }))
  })

  it('Add & Queue submits with queue true', () => {
    const onSubmit = vi.fn()
    renderDrawer('job', onSubmit)
    fireEvent.change(screen.getByPlaceholderText('https://linkedin.com/jobs/view/...'), {
      target: { value: 'https://example.com/job' },
    })
    fireEvent.click(screen.getByText('Add & Queue'))
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ queue: true, job_post_url: 'https://example.com/job' }))
  })
})

describe('CreateEntityDrawer — company mode', () => {
  it('renders the company fields in primary link → name → links → notes order', () => {
    renderDrawer('company')
    expect(screen.getByText('Add Company')).toBeInTheDocument()
    const primary = screen.getByText('Primary Link')
    const name = screen.getByText('Company Name')
    const links = screen.getByText('Additional Links')
    const notes = screen.getByText('Notes')
    const before = (a: Element, b: Element) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0
    expect(before(primary, name)).toBe(true)
    expect(before(name, links)).toBe(true)
    expect(before(links, notes)).toBe(true)
  })

  it('disables submit until a primary link URL is entered', () => {
    renderDrawer('company')
    const addButton = screen.getByText('Add') as HTMLButtonElement
    expect(addButton.disabled).toBe(true)
    fireEvent.change(screen.getByPlaceholderText('Acme GmbH'), {
      target: { value: 'Acme GmbH' },
    })
    expect(addButton.disabled).toBe(true)
    fireEvent.change(screen.getByPlaceholderText('https://acme.example'), {
      target: { value: 'https://acme.example' },
    })
    expect(addButton.disabled).toBe(false)
  })

  it('keeps Add & Process disabled', () => {
    renderDrawer('company')
    const processButton = screen.getByText('Add & Process') as HTMLButtonElement
    expect(processButton.disabled).toBe(true)
    fireEvent.change(screen.getByPlaceholderText('https://acme.example'), {
      target: { value: 'https://acme.example' },
    })
    expect(processButton.disabled).toBe(true)
  })

  it('Add submits name, primary link and queue false', () => {
    const onSubmit = vi.fn()
    renderDrawer('company', onSubmit)
    fireEvent.change(screen.getByPlaceholderText('https://acme.example'), {
      target: { value: 'https://acme.example' },
    })
    fireEvent.change(screen.getByPlaceholderText('Acme GmbH'), {
      target: { value: 'Acme GmbH' },
    })
    fireEvent.click(screen.getByText('Website'))
    fireEvent.click(screen.getByText('Add'))
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      mode: 'company',
      name: 'Acme GmbH',
      queue: false,
      primaryLink: { url: 'https://acme.example', title: 'Website' },
    }))
  })

  it('disables the primary title preset in the additional link selector', () => {
    renderDrawer('company')
    fireEvent.click(screen.getByText('LinkedIn'))
    fireEvent.click(screen.getByText('Add Link'))
    const linkedInButtons = screen.getAllByText('LinkedIn')
    const disabledLinkedIn = linkedInButtons.find((b) => (b as HTMLButtonElement).disabled)
    expect(disabledLinkedIn).toBeTruthy()
    const websiteButtons = screen.getAllByText('Website')
    expect(websiteButtons.every((b) => !(b as HTMLButtonElement).disabled)).toBe(true)
  })

  it('sends the primary link first in the links array', () => {
    const onSubmit = vi.fn()
    renderDrawer('company', onSubmit)
    fireEvent.change(screen.getByPlaceholderText('https://acme.example'), {
      target: { value: 'https://acme.example' },
    })
    fireEvent.click(screen.getByText('Add Link'))
    fireEvent.change(screen.getAllByPlaceholderText('https://...')[0], {
      target: { value: 'https://careers.acme.example' },
    })
    fireEvent.click(screen.getByText('Careers'))
    fireEvent.click(screen.getAllByText('Add')[0])
    fireEvent.click(screen.getByText('Add'))
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      links: [{ url: 'https://careers.acme.example', title: 'Careers' }],
    }))
    const data = (onSubmit.mock.calls[0][0] as CreateEntityFormData)
    expect(data.primaryLink?.url).toBe('https://acme.example')
  })
})

describe('CreateEntityDrawer — clipboard prefill', () => {
  it('prefills the job URL from the clipboard when the drawer opens', async () => {
    readClipboardUrlMock.mockResolvedValue('https://linkedin.com/jobs/view/123')
    renderDrawer('job')
    const urlInput = screen.getByPlaceholderText('https://linkedin.com/jobs/view/...') as HTMLInputElement
    await waitFor(() => expect(urlInput.value).toBe('https://linkedin.com/jobs/view/123'))
  })

  it('prefills the company primary link from the clipboard when the drawer opens', async () => {
    readClipboardUrlMock.mockResolvedValue('https://acme.example')
    renderDrawer('company')
    const urlInput = screen.getByPlaceholderText('https://acme.example') as HTMLInputElement
    await waitFor(() => expect(urlInput.value).toBe('https://acme.example'))
  })

  it('leaves the URL empty when the clipboard has no link', async () => {
    renderDrawer('job')
    const urlInput = screen.getByPlaceholderText('https://linkedin.com/jobs/view/...') as HTMLInputElement
    await waitFor(() => expect(readClipboardUrlMock).toHaveBeenCalled())
    expect(urlInput.value).toBe('')
  })
})
