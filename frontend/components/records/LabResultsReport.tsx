'use client'

import React, { useState } from 'react'
import { toast } from 'sonner'
import { useSaveLab } from '@/hooks/useLabResults'
import type { LabResultsResponse, LabResultInput } from '@/types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Props {
  response: LabResultsResponse
  patientId: string
  patientAge: number
  patientSex: 'male' | 'female' | 'other'
  results: LabResultInput[]
  onSaved?: (reportId: string) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: 'normal' | 'low' | 'high' | 'critical' }) {
  const classes: Record<string, string> = {
    normal:   'bg-green-100 text-green-800',
    low:      'bg-blue-100 text-blue-800',
    high:     'bg-amber-100 text-amber-800',
    critical: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${classes[status]}`}>
      {status === 'critical' && <span aria-hidden="true">⚠</span>}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LabResultsReport({
  response,
  patientId,
  patientAge,
  patientSex,
  results,
  onSaved,
}: Props) {
  const saveLab = useSaveLab()
  const [saved, setSaved] = useState(false)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())

  // ── Row expand/collapse ──────────────────────────────────────────────────

  function toggleRow(index: number) {
    setExpandedRows((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  // ── Save ─────────────────────────────────────────────────────────────────

  function handleSave() {
    saveLab.mutate(
      {
        patientId,
        results,
        reportDate: new Date().toISOString().split('T')[0],
        labName: 'Manual Entry',
        patientAge,
        patientSex,
      },
      {
        onSuccess: (data) => {
          setSaved(true)
          toast.success('Saved to your records')
          onSaved?.(data.id)
        },
        onError: () => toast.error('Failed to save'),
      }
    )
  }

  // ── Share (copy to clipboard) ─────────────────────────────────────────────

  function handleShare() {
    const today = new Date().toISOString().split('T')[0]

    const resultsLines = response.results
      .map((r) => `${r.testName}: ${r.value} ${r.unit} — ${r.status}`)
      .join('\n')

    const criticalLine =
      response.criticalFlags.length > 0
        ? response.criticalFlags.join(' / ')
        : 'None'

    const patternsLine =
      response.patternsDetected.length > 0
        ? response.patternsDetected.join(' / ')
        : 'None'

    const followUpLine =
      response.followUpTests.length > 0
        ? response.followUpTests.join(' / ')
        : 'None'

    const text = [
      `Lab Results Summary — ${today}`,
      '',
      response.summary,
      '',
      'Results:',
      resultsLines,
      '',
      `Critical Flags: ${criticalLine}`,
      '',
      `Patterns: ${patternsLine}`,
      '',
      `Follow-up Tests: ${followUpLine}`,
      '',
      `⚕ ${response.disclaimer}`,
    ].join('\n')

    navigator.clipboard.writeText(text).then(() => {
      toast.success('Copied to clipboard')
    }).catch(() => toast.error('Could not copy to clipboard'))
  }

  // ── Download PDF ──────────────────────────────────────────────────────────

  function handleDownloadPdf() {
    toast('Coming soon — PDF download will be available in a future update')
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-6">

      {/* 1. Critical Alerts Banner */}
      {response.criticalFlags.length > 0 && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-4">
          <p className="text-red-800 font-semibold flex items-center gap-2 mb-2">
            <span aria-hidden="true">⚠</span>
            Critical values detected — seek immediate medical attention
          </p>
          <ul className="list-disc list-inside space-y-1">
            {response.criticalFlags.map((flag, i) => (
              <li key={i} className="text-red-800 text-sm">
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 2. Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
              <th className="text-left px-3 py-2 font-medium">Test</th>
              <th className="text-left px-3 py-2 font-medium">Value</th>
              <th className="text-left px-3 py-2 font-medium">Unit</th>
              <th className="text-left px-3 py-2 font-medium">Reference Range</th>
              <th className="text-left px-3 py-2 font-medium">Status</th>
              <th className="text-left px-3 py-2 font-medium">Explanation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {response.results.map((result, i) => {
              const isExpanded = expandedRows.has(i)
              const rowBg =
                result.status === 'critical'
                  ? 'bg-red-50'
                  : result.actionNeeded
                  ? 'bg-amber-50'
                  : ''

              return (
                <React.Fragment key={i}>
                  <tr
                    className={`cursor-pointer hover:brightness-95 transition-colors ${rowBg}`}
                    onClick={() => toggleRow(i)}
                    tabIndex={0}
                    role="button"
                    aria-expanded={expandedRows.has(i)}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleRow(i) } }}
                  >
                    <td className="px-3 py-2 font-medium text-gray-900">{result.testName}</td>
                    <td className="px-3 py-2 text-gray-700">{result.value}</td>
                    <td className="px-3 py-2 text-gray-500">{result.unit}</td>
                    <td className="px-3 py-2 text-gray-500">{result.referenceRange}</td>
                    <td className="px-3 py-2">
                      <StatusBadge status={result.status} />
                    </td>
                    <td className="px-3 py-2 text-gray-400">
                      <span aria-label={isExpanded ? 'Collapse' : 'Expand'}>
                        {isExpanded ? '▼' : '▶'}
                      </span>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr className={rowBg}>
                      <td colSpan={6} className="px-4 py-3 text-sm text-gray-600">
                        {result.explanation}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* 3. Summary Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900 mb-1">Summary</h2>
          <p className="text-sm text-gray-700 leading-relaxed">{response.summary}</p>
        </div>

        {response.patternsDetected.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800 mb-1">Patterns Detected</h3>
            <ul className="list-disc list-inside space-y-1">
              {response.patternsDetected.map((pattern, i) => (
                <li key={i} className="text-sm text-gray-700">
                  {pattern}
                </li>
              ))}
            </ul>
          </div>
        )}

        {response.followUpTests.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800 mb-1">Suggested Follow-up Tests</h3>
            <ul className="list-disc list-inside space-y-1">
              {response.followUpTests.map((test, i) => (
                <li key={i} className="text-sm text-gray-700 flex items-center gap-2">
                  {test}
                  <span className="ml-2 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded px-2 py-0.5">
                    Ask doctor about this
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 4. Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saveLab.isPending || saved}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saveLab.isPending && <Spinner />}
          {saved ? 'Saved' : 'Save to my records'}
        </button>

        <button
          type="button"
          onClick={handleShare}
          className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Share with doctor
        </button>

        <button
          type="button"
          onClick={handleDownloadPdf}
          className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Download PDF
        </button>
      </div>

      {/* 5. Footer Disclaimer */}
      <p className="text-xs text-gray-400 italic mt-4 pt-4 border-t">
        {response.disclaimer}
      </p>
    </div>
  )
}
