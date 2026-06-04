'use client'

import { useMemo, useState } from 'react'
import {
  Calendar,
  ChevronDown,
  FlaskConical,
  GitCompareArrows,
  AlertCircle,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import EmptyState from '@/components/ui/EmptyState'
import { cn } from '@/lib/utils'
import { useLabResultsHistory } from '@/hooks/useLabResults'
import LabResultsReport from './LabResultsReport'
import type {
  LabResultStatus,
  LabResultsResponse,
  SavedLabResultSet,
} from '@/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

const STATUS_COLOR: Record<LabResultStatus, string> = {
  normal: 'text-green-600',
  low: 'text-blue-600',
  high: 'text-amber-600',
  critical: 'text-red-600',
}

/** A saved set carries already-interpreted results; reconstruct the report
 *  shape the report component expects (summary etc. aren't persisted). */
function toReport(set: SavedLabResultSet): LabResultsResponse {
  return {
    results: set.results,
    summary: '',
    patterns_detected: [],
    critical_flags: set.critical_flags ?? [],
    follow_up_tests: [],
    disclaimer:
      'This is an educational interpretation of previously saved results, not a medical diagnosis. Consult a qualified clinician.',
  }
}

// ---------------------------------------------------------------------------
// Compare view — same test across two saved sets
// ---------------------------------------------------------------------------

function CompareView({
  a,
  b,
  onClose,
}: {
  a: SavedLabResultSet
  b: SavedLabResultSet
  onClose: () => void
}) {
  const rows = useMemo(() => {
    const names = new Set<string>()
    a.results.forEach((r) => names.add(r.test_name))
    b.results.forEach((r) => names.add(r.test_name))
    return Array.from(names).map((name) => ({
      name,
      a: a.results.find((r) => r.test_name === name),
      b: b.results.find((r) => r.test_name === name),
    }))
  }, [a, b])

  return (
    <div className="rounded-xl border border-gray-200 bg-white">
      <div className="flex items-center justify-between border-b border-gray-100 p-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <GitCompareArrows className="h-4 w-4 text-teal-600" />
          Comparison
        </h3>
        <button
          onClick={onClose}
          aria-label="Close comparison"
          className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <table className="w-full">
        <thead>
          <tr className="text-left text-[11px] font-medium uppercase tracking-wide text-gray-400">
            <th className="py-2.5 pl-4 pr-2">Test</th>
            <th className="px-2 py-2.5">{formatDate(a.report_date)}</th>
            <th className="px-2 py-2.5">{formatDate(b.report_date)}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name} className="border-t border-gray-100">
              <td className="py-2.5 pl-4 pr-2 text-sm font-medium text-gray-900">
                {row.name}
              </td>
              <td className="px-2 py-2.5 text-sm">
                {row.a ? (
                  <span className={cn('tabular-nums', STATUS_COLOR[row.a.status])}>
                    {row.a.value} {row.a.unit}
                  </span>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              <td className="px-2 py-2.5 text-sm">
                {row.b ? (
                  <span className={cn('tabular-nums', STATUS_COLOR[row.b.status])}>
                    {row.b.value} {row.b.unit}
                  </span>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// History list
// ---------------------------------------------------------------------------

interface LabResultsHistoryProps {
  patientId: string
}

export default function LabResultsHistory({ patientId }: LabResultsHistoryProps) {
  const { data, isLoading, isError, error, refetch } =
    useLabResultsHistory(patientId)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [compareMode, setCompareMode] = useState(false)
  const [selected, setSelected] = useState<string[]>([])

  const sets = data ?? []
  const compareReady = selected.length === 2
  const setA = sets.find((s) => s.id === selected[0])
  const setB = sets.find((s) => s.id === selected[1])

  function toggleSelect(id: string) {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= 2) return [prev[1], id] // keep most recent two
      return [...prev, id]
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error?.message || 'Could not load your saved lab results.'}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="mt-3"
        >
          Try again
        </Button>
      </div>
    )
  }

  if (sets.length === 0) {
    return (
      <EmptyState
        icon={<FlaskConical className="h-6 w-6" />}
        title="No saved lab results yet"
        description="Interpret a set of results and save it to build your history."
      />
    )
  }

  return (
    <div className="space-y-3">
      {/* Compare toolbar */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-400">
          {sets.length} saved {sets.length === 1 ? 'set' : 'sets'}
        </p>
        <Button
          variant={compareMode ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            setCompareMode((m) => !m)
            setSelected([])
            setExpanded(null)
          }}
          className={compareMode ? 'bg-teal-600 hover:bg-teal-700' : ''}
        >
          <GitCompareArrows className="h-4 w-4" />
          {compareMode ? 'Cancel compare' : 'Compare'}
        </Button>
      </div>

      {compareMode && (
        <p className="rounded-lg bg-teal-50 px-3 py-2 text-xs text-teal-700">
          Select two reports to compare the same tests side by side.
          {selected.length > 0 && ` (${selected.length}/2 selected)`}
        </p>
      )}

      {/* Comparison panel */}
      {compareMode && compareReady && setA && setB && (
        <CompareView a={setA} b={setB} onClose={() => setSelected([])} />
      )}

      {/* List */}
      {sets.map((set) => {
        const isOpen = expanded === set.id
        const isSelected = selected.includes(set.id)
        const hasCritical = (set.critical_flags?.length ?? 0) > 0

        return (
          <div
            key={set.id}
            className={cn(
              'overflow-hidden rounded-xl border bg-white transition-colors',
              isSelected ? 'border-teal-400 ring-1 ring-teal-200' : 'border-gray-200'
            )}
          >
            <button
              onClick={() =>
                compareMode
                  ? toggleSelect(set.id)
                  : setExpanded(isOpen ? null : set.id)
              }
              className="flex w-full items-center gap-3 p-4 text-left hover:bg-gray-50"
            >
              {compareMode && (
                <span
                  className={cn(
                    'flex h-5 w-5 shrink-0 items-center justify-center rounded border',
                    isSelected
                      ? 'border-teal-600 bg-teal-600 text-white'
                      : 'border-gray-300'
                  )}
                >
                  {isSelected && <span className="text-xs">✓</span>}
                </span>
              )}

              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
                <Calendar className="h-5 w-5" />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-semibold text-gray-900">
                    {set.lab_name || 'Lab report'}
                  </p>
                  {hasCritical && (
                    <span
                      className="h-2 w-2 shrink-0 rounded-full bg-red-500"
                      title="Critical values flagged"
                    />
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  {formatDate(set.report_date)} · {set.results.length}{' '}
                  {set.results.length === 1 ? 'test' : 'tests'}
                </p>
              </div>

              {hasCritical && (
                <Badge
                  variant="outline"
                  className="hidden border-red-200 bg-red-50 text-red-600 sm:inline-flex"
                >
                  Critical
                </Badge>
              )}

              {!compareMode && (
                <ChevronDown
                  className={cn(
                    'h-4 w-4 shrink-0 text-gray-400 transition-transform',
                    isOpen && 'rotate-180'
                  )}
                />
              )}
            </button>

            {!compareMode && isOpen && (
              <div className="border-t border-gray-100 bg-gray-50/40 p-4">
                <LabResultsReport report={toReport(set)} embedded />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
