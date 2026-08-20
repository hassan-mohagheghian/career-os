import { describe, it, expect } from 'vitest'
import { extractUrlFromDataTransfer, isUrlString, dataTransferHasUrl } from './url-drag'

function fakeDataTransfer(types: string[], values: Record<string, string>) {
  return {
    types,
    getData: (type: string) => values[type] ?? '',
  } as unknown as DataTransfer
}

describe('isUrlString', () => {
  it('accepts http and https urls', () => {
    expect(isUrlString('https://example.com/job')).toBe(true)
    expect(isUrlString('http://localhost:5000/apply')).toBe(true)
  })
  it('rejects non-urls', () => {
    expect(isUrlString('not a url')).toBe(false)
    expect(isUrlString('')).toBe(false)
    expect(isUrlString('ftp://example.com')).toBe(false)
  })
})

describe('extractUrlFromDataTransfer', () => {
  it('reads the first url from text/uri-list', () => {
    const dt = fakeDataTransfer(['text/uri-list'], {
      'text/uri-list': 'https://example.com/job\nhttps://example.com/other',
    })
    expect(extractUrlFromDataTransfer(dt)).toBe('https://example.com/job')
  })

  it('skips comment lines and blank lines in uri-list', () => {
    const dt = fakeDataTransfer(['text/uri-list'], {
      'text/uri-list': '# comment\n\nhttps://example.com/job',
    })
    expect(extractUrlFromDataTransfer(dt)).toBe('https://example.com/job')
  })

  it('falls back to text/plain', () => {
    const dt = fakeDataTransfer(['text/plain'], { 'text/plain': 'https://example.com/job' })
    expect(extractUrlFromDataTransfer(dt)).toBe('https://example.com/job')
  })

  it('returns null when nothing is a url', () => {
    const dt = fakeDataTransfer(['text/plain'], { 'text/plain': 'hello world' })
    expect(extractUrlFromDataTransfer(dt)).toBeNull()
  })

  it('returns null for null/undefined dataTransfer', () => {
    expect(extractUrlFromDataTransfer(null)).toBeNull()
    expect(extractUrlFromDataTransfer(undefined)).toBeNull()
  })
})

describe('dataTransferHasUrl', () => {
  it('detects uri-list and text/plain', () => {
    expect(dataTransferHasUrl(fakeDataTransfer(['text/uri-list'], {}))).toBe(true)
    expect(dataTransferHasUrl(fakeDataTransfer(['text/plain'], {}))).toBe(true)
    expect(dataTransferHasUrl(fakeDataTransfer(['Files'], {}))).toBe(false)
  })
  it('returns false for null', () => {
    expect(dataTransferHasUrl(null)).toBe(false)
  })
})