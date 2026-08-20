import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DropJobOverlay } from './DropJobOverlay'

function urlDataTransfer(url: string): DataTransfer {
  const values: Record<string, string> = {
    'text/uri-list': url,
    'text/plain': url,
  }
  return {
    types: Object.keys(values),
    getData: (type: string) => values[type] ?? '',
    dropEffect: '',
  } as unknown as DataTransfer
}

describe('DropJobOverlay', () => {
  it('shows the drop hint while a url is dragged over the page', () => {
    const onDropUrl = vi.fn()
    render(
      <DropJobOverlay onDropUrl={onDropUrl}>
        <div>page content</div>
      </DropJobOverlay>
    )
    fireEvent.dragEnter(screen.getByText('page content'), { dataTransfer: urlDataTransfer('https://example.com/job') })
    fireEvent.dragOver(screen.getByText('page content'), { dataTransfer: urlDataTransfer('https://example.com/job') })
    expect(screen.getByText('Drop to add job')).toBeInTheDocument()
  })

  it('calls onDropUrl with the dropped url', () => {
    const onDropUrl = vi.fn()
    render(
      <DropJobOverlay onDropUrl={onDropUrl}>
        <div>page content</div>
      </DropJobOverlay>
    )
    fireEvent.drop(screen.getByText('page content'), { dataTransfer: urlDataTransfer('https://example.com/job') })
    expect(onDropUrl).toHaveBeenCalledWith('https://example.com/job')
  })

  it('ignores drops without a url', () => {
    const onDropUrl = vi.fn()
    render(
      <DropJobOverlay onDropUrl={onDropUrl}>
        <div>page content</div>
      </DropJobOverlay>
    )
    const dt = { types: ['Files'], getData: () => '' } as unknown as DataTransfer
    fireEvent.drop(screen.getByText('page content'), { dataTransfer: dt })
    expect(onDropUrl).not.toHaveBeenCalled()
  })
})