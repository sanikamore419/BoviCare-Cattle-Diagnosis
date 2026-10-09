import assert from 'node:assert/strict'
import test from 'node:test'
import {
  formatIstDateTime,
  getWaitHours,
  parseTimestamp,
  sortCasesByPriorityAndSubmission,
  timestampMillis,
} from './dateTime.js'

test('formats a UTC timestamp as the expected IST date and time', () => {
  assert.equal(
    formatIstDateTime('2026-10-09T05:45:00Z'),
    '09 Oct 2026, 11:15 AM IST',
  )
})

test('interprets legacy timezone-naive timestamps as UTC without changing their instant', () => {
  const parsed = parseTimestamp('2026-10-09 05:45:00.000000')
  assert.equal(parsed?.toISOString(), '2026-10-09T05:45:00.000Z')
  assert.equal(formatIstDateTime('2026-10-09 05:45:00'), '09 Oct 2026, 11:15 AM IST')
})

test('uses one timestamp presentation for dashboard, details, and timeline values', () => {
  const caseTimestamp = '2026-10-09T05:45:00+00:00'
  const eventTimestamp = '2026-10-09 05:45:00'
  assert.equal(formatIstDateTime(caseTimestamp), formatIstDateTime(eventTimestamp))
})

test('handles missing and invalid timestamps without throwing', () => {
  assert.equal(formatIstDateTime(null), 'N/A')
  assert.equal(formatIstDateTime('not a timestamp'), 'N/A')
  assert.equal(timestampMillis('not a timestamp'), null)
  assert.equal(getWaitHours(undefined, Date.parse('2026-10-09T06:45:00Z')), 0)
})

test('calculates waiting hours using UTC instants and clamps future timestamps', () => {
  const now = Date.parse('2026-10-09T06:45:00Z')
  assert.equal(getWaitHours('2026-10-09 05:45:00', now), 1)
  assert.equal(getWaitHours('2026-10-09T07:00:00Z', now), 0)
})

test('sorts newest first within HIGH, MEDIUM, LOW priority groups and leaves invalid dates last', () => {
  const cases = [
    { id: 1, urgency_level: 'MEDIUM', created_at: '2026-10-09T05:45:00Z' },
    { id: 2, urgency_level: 'HIGH', created_at: '2026-10-09T05:00:00Z' },
    { id: 3, urgency_level: 'HIGH', created_at: '2026-10-09T05:45:00Z' },
    { id: 4, urgency_level: 'LOW', created_at: null },
    { id: 5, urgency_level: 'LOW', created_at: '2026-10-09T05:45:00Z' },
  ]
  assert.deepEqual(
    sortCasesByPriorityAndSubmission(cases).map(({ id }) => id),
    [3, 2, 1, 5, 4],
  )
})
