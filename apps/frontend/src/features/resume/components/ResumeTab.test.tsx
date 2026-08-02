import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import ResumeTab from './ResumeTab'

describe('ResumeTab', () => {
  const defaultProps = {
    resumes: [],
    linkedinProfiles: [],
    onRefreshResumes: vi.fn(),
    onRefreshLinkedin: vi.fn(),
  }

  it('renders Profile & Resume header', () => {
    render(<ResumeTab {...defaultProps} />)
    expect(screen.getByText('Profile & Resume')).toBeInTheDocument()
  })

  it('renders Resumes tab', () => {
    render(<ResumeTab {...defaultProps} />)
    expect(screen.getByText('Resumes')).toBeInTheDocument()
  })

  it('renders LinkedIn Profile tab', () => {
    render(<ResumeTab {...defaultProps} />)
    expect(screen.getByText('LinkedIn Profile')).toBeInTheDocument()
  })

  it('renders empty state when no resumes', () => {
    render(<ResumeTab {...defaultProps} />)
    expect(screen.getByText('No resumes uploaded yet.')).toBeInTheDocument()
  })

  it('renders Upload Resume button', () => {
    render(<ResumeTab {...defaultProps} />)
    expect(screen.getAllByText('Upload Resume').length).toBeGreaterThanOrEqual(1)
  })

  it('opens upload dialog when Upload Resume clicked', async () => {
    const user = userEvent.setup()
    render(<ResumeTab {...defaultProps} />)
    await user.click(screen.getAllByText('Upload Resume')[0])
    expect(screen.getByText(/Paste your resume text below/)).toBeInTheDocument()
  })

  it('renders resume list when resumes provided', () => {
    const resumes = [
      { id: 'original_1', version: 1, created_at: '2026-07-20T10:00:00Z', content: '<p>Resume content</p>' },
    ]
    render(<ResumeTab {...defaultProps} resumes={resumes} />)
    expect(screen.getByText('v1')).toBeInTheDocument()
  })

  it('renders linkedin profiles', () => {
    const profiles = [
      { id: 'linkedin_1', version: 1, created_at: '2026-07-20T10:00:00Z', content: '<p>Profile</p>' },
    ]
    render(<ResumeTab {...defaultProps} linkedinProfiles={profiles} />)
    expect(screen.getByText('LinkedIn Profile')).toBeInTheDocument()
  })

  it('switches to LinkedIn tab', async () => {
    const user = userEvent.setup()
    render(<ResumeTab {...defaultProps} />)
    await user.click(screen.getByRole('tab', { name: /LinkedIn Profile/ }))
    expect(screen.getByText(/Paste your LinkedIn profile text/)).toBeInTheDocument()
  })

  it('renders privacy warning on LinkedIn tab', async () => {
    const user = userEvent.setup()
    render(<ResumeTab {...defaultProps} />)
    await user.click(screen.getByRole('tab', { name: /LinkedIn Profile/ }))
    expect(screen.getByText(/Personal info.*automatically masked/)).toBeInTheDocument()
  })

  it('opens LinkedIn upload dialog', async () => {
    const user = userEvent.setup()
    render(<ResumeTab {...defaultProps} />)
    await user.click(screen.getByRole('tab', { name: /LinkedIn Profile/ }))
    await user.click(screen.getAllByText('Upload Profile')[0])
    expect(screen.getByText(/Paste your LinkedIn profile text below/)).toBeInTheDocument()
  })

  it('renders delete button for resumes', () => {
    const resumes = [
      { id: 'original_1', version: 1, created_at: '2026-07-20T10:00:00Z', content: '<p>Resume</p>' },
    ]
    render(<ResumeTab {...defaultProps} resumes={resumes} />)
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('renders Active badge for latest resume', () => {
    const resumes = [
      { id: 'original_1', version: 1, created_at: '2026-07-20T10:00:00Z', content: '<p>Resume</p>' },
    ]
    render(<ResumeTab {...defaultProps} resumes={resumes} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })
})
