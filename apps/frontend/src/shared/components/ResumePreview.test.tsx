import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ResumePreview from './ResumePreview'

describe('ResumePreview', () => {
  it('renders No content when html is empty', () => {
    render(<ResumePreview html="" />)
    expect(screen.getByText('No content')).toBeInTheDocument()
  })

  it('renders No content when html is null', () => {
    render(<ResumePreview html={null} />)
    expect(screen.getByText('No content')).toBeInTheDocument()
  })

  it('renders cleaned HTML content', () => {
    render(<ResumePreview html="<h1>Hello World</h1>" />)
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('strips style tags', () => {
    render(<ResumePreview html="<style>.red{color:red}</style><p>Content</p>" />)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('strips inline style attributes', () => {
    render(<ResumePreview html='<p style="color:red">Styled</p>' />)
    expect(screen.getByText('Styled')).toBeInTheDocument()
  })

  it('strips html/head/body wrapper tags', () => {
    render(<ResumePreview html="<html><head></head><body><p>Inner</p></body></html>" />)
    expect(screen.getByText('Inner')).toBeInTheDocument()
  })

  it('strips meta and link tags', () => {
    render(<ResumePreview html='<meta charset="utf-8"><link rel="stylesheet" href="style.css"><p>Content</p>' />)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<ResumePreview html="<p>Test</p>" className="custom" />)
    expect(container.querySelector('.custom')).toBeInTheDocument()
  })

  it('renders empty content gracefully', () => {
    render(<ResumePreview html="   " />)
    expect(screen.getByText('No content')).toBeInTheDocument()
  })
})
