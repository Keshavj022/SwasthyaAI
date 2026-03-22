'use client'

import { useState } from 'react'
import { labResultsApi } from '@/lib/api'
import { useLabHistory } from '@/hooks/useLabResults'
import type { LabResultsResponse, SavedLabReport, LabResultInput } from '@/types'
import LabResultsReport from './LabResultsReport'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Props {
  patientId: string
  patientAge: number
  patientSex: 'male' | 'female' | 'other'
}

type ComparisonRow = {
  testName: string
  report1Value: string
  report2Value: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function buildComparisonRows(r1: SavedLabReport, r2: SavedLabReport): ComparisonRow[] {
  const allNames = new Set<string>()
  r1.results.forEach((r) => allNames.add(r.testName))
  r2.results.forEach((r) => allNames.add(r.testName))

  return Array.from(allNames).map((testName) => {
    const t1 = r1.results.find((r) => r.testName === testName)
    const t2 = r2.results.find((r) => r.testName === testName)
    const fmt = (t: { value: number; unit: string } | undefined) =>
      t ? `${t.value}${t.unit ? ' ' + t.unit : ''}` : '—'
    return { testName, report1Value: fmt(t1), report2Value: fmt(t2) }
  })
}

// ---------------------------------------------------------------------------
// Skeleton row
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <div className="border rounded-lg p-4 bg-white mb-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-3 bg-gray-100 rounded w-1/4" />
        </div>
        <div className="h-3 bg-gray-100 rounded w-16" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LabResultsHistory({ patientId, patientAge, patientSex }: Props) {
  const { data: reports, isLoading } = useLabHistory(patientId)

  // Expanded report ids
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  // Cache of interpreted responses keyed by report id
  const [interpretCache, setInterpretCache] = useState<Map<string, LabResultsResponse>>(new Map())

  // Loading state per report id (while interpreting)
  const [interpretingIds, setInterpretingIds] = useState<Set<string>>(new Set())

  // Per-ID error state
  const [errorIds, setErrorIds] = useState<Set<string>>(new Set())

  // In-flight guard to prevent duplicate concurrent calls
  const [inFlightIds, setInFlightIds] = useState<Set<string>>(new Set())

  // Compare mode: selected report ids (up to 2)
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([])
  const [compareMode, setCompareMode] = useState(false)

  // ── Expand / collapse ────────────────────────────────────────────────────

  async function toggleExpand(report: SavedLabReport) {
    const id = report.id

    // Collapse path: always allowed
    if (expandedIds.has(id)) {
      setExpandedIds((prev) => { const n = new Set(prev); n.delete(id); return n })
      return
    }

    // Expand path: guard against duplicate concurrent calls
    setExpandedIds((prev) => new Set(prev).add(id))
    if (interpretCache.has(id) || inFlightIds.has(id)) return

    setInFlightIds((prev) => new Set(prev).add(id))
    setInterpretingIds((prev) => new Set(prev).add(id))
    try {
      const inputs: LabResultInput[] = report.results.map((r) => ({
        testName: r.testName,
        value: r.value,
        unit: r.unit,
        date: r.date,
      }))
      const response = await labResultsApi.interpret({
        results: inputs,
        patientId,
        patientAge,
        patientSex,
      })
      setInterpretCache((prev) => new Map(prev).set(id, response))
      setErrorIds((prev) => { const next = new Set(prev); next.delete(id); return next })
    } catch {
      setErrorIds((prev) => new Set(prev).add(id))
    } finally {
      setInFlightIds((prev) => { const n = new Set(prev); n.delete(id); return n })
      setInterpretingIds((prev) => { const n = new Set(prev); n.delete(id); return n })
    }
  }

  // ── Compare mode ─────────────────────────────────────────────────────────

  function handleCompareToggle(id: string) {
    setSelectedForCompare((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= 2) return [prev[1], id]
      return [...prev, id]
    })
  }

  function cancelCompare() {
    setCompareMode(false)
    setSelectedForCompare([])
  }

  // ── Render ────────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="mt-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Lab Results History</h2>
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    )
  }

  if (!reports || reports.length === 0) {
    return (
      <div className="mt-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Lab Results History</h2>
        <p className="text-sm text-gray-500">
          No lab results saved yet. Use the form above to interpret and save your results.
        </p>
      </div>
    )
  }

  const canCompare = reports.length >= 2

  // Build comparison panel data when 2 are selected
  let comparisonRows: ComparisonRow[] | null = null
  if (selectedForCompare.length === 2) {
    const r1 = reports.find((r) => r.id === selectedForCompare[0])
    const r2 = reports.find((r) => r.id === selectedForCompare[1])
    if (r1 && r2) comparisonRows = buildComparisonRows(r1, r2)
  }

  // Derive comparison report objects for the panel
  const compareReport1 = selectedForCompare.length === 2 ? reports.find((r) => r.id === selectedForCompare[0]) : undefined
  const compareReport2 = selectedForCompare.length === 2 ? reports.find((r) => r.id === selectedForCompare[1]) : undefined

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Lab Results History</h2>
        {canCompare && !compareMode && (
          <button
            type="button"
            onClick={() => setCompareMode(true)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Compare results
          </button>
        )}
        {compareMode && (
          <button
            type="button"
            onClick={cancelCompare}
            className="text-sm text-gray-500 hover:text-gray-700 font-medium"
          >
            Cancel compare
          </button>
        )}
      </div>

      {compareMode && (
        <p className="text-xs text-gray-500 mb-3">
          Select 2 reports to compare side by side.
          {selectedForCompare.length === 1 && ' Select one more.'}
        </p>
      )}

      {/* Report list */}
      {reports.map((report) => {
        const isExpanded = expandedIds.has(report.id)
        const isInterpreting = interpretingIds.has(report.id)
        const interpreted = interpretCache.get(report.id)
        const isSelected = selectedForCompare.includes(report.id)

        const inputs: LabResultInput[] = report.results.map((r) => ({
          testName: r.testName,
          value: r.value,
          unit: r.unit,
          date: r.date,
        }))

        return (
          <div
            key={report.id}
            className={`border rounded-lg p-4 bg-white mb-3 transition-colors ${
              compareMode && isSelected ? 'border-blue-400 ring-1 ring-blue-300' : 'border-gray-200'
            }`}
          >
            {/* Header row */}
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-gray-900">
                    {formatDate(report.reportDate)}
                  </span>
                  {report.hasCritical && (
                    <span
                      className="inline-block w-2 h-2 rounded-full bg-red-500 ml-2"
                      title="Contains critical values"
                    />
                  )}
                </div>
                <div className="mt-0.5 flex items-center gap-3 text-xs text-gray-500">
                  <span>{report.labName || 'Manual Entry'}</span>
                  <span>{report.testCount} tests</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 ml-3">
                {compareMode && (
                  <button
                    type="button"
                    onClick={() => handleCompareToggle(report.id)}
                    className={`text-xs px-2 py-1 rounded border font-medium transition-colors ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'text-blue-600 border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    {isSelected ? 'Selected' : 'Select'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => toggleExpand(report)}
                  className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                  aria-expanded={isExpanded}
                >
                  {isExpanded ? '▼ Hide' : '▶ View'}
                </button>
              </div>
            </div>

            {/* Expanded body */}
            {isExpanded && (
              <div className="mt-4">
                {isInterpreting && (
                  <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
                    <svg
                      className="animate-spin h-4 w-4 text-gray-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Interpreting results…
                  </div>
                )}
                {!isInterpreting && interpreted && (
                  <LabResultsReport
                    response={interpreted}
                    patientId={patientId}
                    patientAge={patientAge}
                    patientSex={patientSex}
                    results={inputs}
                  />
                )}
                {!isInterpreting && errorIds.has(report.id) && (
                  <p className="text-sm text-red-500">Failed to load interpretation. Collapse and try again.</p>
                )}
              </div>
            )}
          </div>
        )
      })}

      {/* Comparison panel */}
      {comparisonRows && compareReport1 && compareReport2 && (
        <div className="mt-6 border border-gray-200 rounded-xl bg-white p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">
            Comparing: {formatDate(compareReport1.reportDate)} vs {formatDate(compareReport2.reportDate)}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                  <th className="text-left px-3 py-2 font-medium">Test</th>
                  <th className="text-left px-3 py-2 font-medium">{formatDate(compareReport1.reportDate)}</th>
                  <th className="text-left px-3 py-2 font-medium">{formatDate(compareReport2.reportDate)}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {comparisonRows.map((row) => (
                  <tr key={row.testName}>
                    <td className="px-3 py-2 font-medium text-gray-900">{row.testName}</td>
                    <td className="px-3 py-2 text-gray-700">{row.report1Value}</td>
                    <td className="px-3 py-2 text-gray-700">{row.report2Value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
