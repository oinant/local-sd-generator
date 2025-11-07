import { describe, it, expect } from 'vitest'
import { formatSessionName, formatDate, formatDateShort } from '@/utils/formatters'

describe('formatSessionName', () => {
  it('formats old format (YYYY-MM-DD_HHMMSS_name.prompt)', () => {
    const input = '2025-10-14_173320_hassaku_actualportrait.prompt'
    const expected = '2025-10-14 · hassaku_actualportrait'
    expect(formatSessionName(input)).toBe(expected)
  })

  it('formats new format (YYYYMMDD_HHMMSS-name)', () => {
    const input = '20251014_173320-Hassaku-fantasy-default'
    const expected = '2025-10-14 · Hassaku fantasy default'
    expect(formatSessionName(input)).toBe(expected)
  })

  it('returns input as-is if format unrecognized', () => {
    const input = 'unknown_format_123'
    expect(formatSessionName(input)).toBe(input)
  })

  it('handles edge case with empty string', () => {
    const input = ''
    expect(formatSessionName(input)).toBe(input)
  })

  it('removes .prompt extension in old format', () => {
    const input = '2025-11-07_143000_test.prompt'
    const expected = '2025-11-07 · test'
    expect(formatSessionName(input)).toBe(expected)
  })

  it('replaces dashes with spaces in new format', () => {
    const input = '20251107_143000-multi-word-name'
    const expected = '2025-11-07 · multi word name'
    expect(formatSessionName(input)).toBe(expected)
  })
})

describe('formatDate', () => {
  it('formats date with French locale', () => {
    const date = new Date('2025-11-07T14:30:00')
    const result = formatDate(date)
    // French locale format: "7 nov. 2025, 14:30"
    expect(result).toMatch(/7 nov\. 2025.*14:30/)
  })

  it('formats date at midnight', () => {
    const date = new Date('2025-01-01T00:00:00')
    const result = formatDate(date)
    expect(result).toMatch(/1 janv\. 2025/)
  })
})

describe('formatDateShort', () => {
  it('formats date without time', () => {
    const date = new Date('2025-11-07T14:30:00')
    const result = formatDateShort(date)
    // French locale format: "7 nov. 2025" (no time)
    expect(result).toMatch(/7 nov\. 2025/)
    expect(result).not.toContain('14:30')
  })
})
