'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  ChevronDown,
  Copy,
  Download,
  Save,
  Lightbulb,
  ClipboardList,
  Loader2,
  CheckCircle2,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useSaveLabResults } from '@/hooks/useLabResults'
import type {
  InterpretedLabResult,
  LabResultInput,
  LabResultsResponse,
  LabResultStatus,
} from '@/types'

// ---------------------------------------------------------------------------
// Status styling
// ---------------------------------------------------------------------------

const STATUS_STYLES: Record<
  LabResultStatus,
  { label: string; badge: string; dot: string }
> = {
  normal: {
    label: 'Normal',
    badge: 'bg-green-100 text-green-700 border-green-200',
    dot: 'bg-green-500',
  },
  low: {
    label: 'Low',
    badge: 'bg-blue-100 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
  },
  high: {
    label: 'High',
    badge: 'bg-amber-100 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
  },
  critical: {
    label: 'Critical',
    badge: 'bg-red-100 text-red-700 border-red-200',
    dot: 'bg-red-500',
  },
}

function StatusBadge({ status }: { status: LabResultStatus }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.normal
  return (
    <Badge
      variant="outline"
      className={cn('gap-1 font-medium', s.badge)}
    >
      {status === 'critical' && <AlertTriangle className="h-3 w-3" />}
      {s.label}
    </Badge>
  )
}

// ---------------------------------------------------------------------------
// Formatted text summary (for clipboard sharing)
// ---------------------------------------------------------------------------

function formatForSharing(r: LabResultsResponse): string {
  const lines: string[] = ['Lab Results Summary', '===================', '']
  for (const res of r.results) {
    lines.push(
      `- ${res.test_name}: ${res.value} ${res.unit} [${STATUS_STYLES[res.status]?.label ?? res.status}] (ref: ${res.reference_range})`
    )
  }
  lines.push('')
  if (r.critical_flags.length) {
    lines.push('CRITICAL FLAGS:')
    r.critical_flags.forEach((f) => lines.push(`! ${f}`))
    lines.push('')
  }
  if (r.summary) {
    lines.push('Summary:', r.summary, '')
  }
  if (r.patterns_detected.length) {
    lines.push('Patterns detected:')
    r.patterns_detected.forEach((p) => lines.push(`- ${p}`))
    lines.push('')
  }
  if (r.follow_up_tests.length) {
    lines.push('Suggested follow-up tests:')
    r.follow_up_tests.forEach((t) => lines.push(`- ${t}`))
    lines.push('')
  }
  lines.push(r.disclaimer)
  return lines.join('\n')
}

// ---------------------------------------------------------------------------
// Results table (with row expansion)
// ---------------------------------------------------------------------------

function ResultRow({ result }: { result: InterpretedLabResult }) {
  const [open, setOpen] = useState(false)
  const actionBg = result.action_needed ? 'bg-amber-50/70' : ''

  return (
    <>
      <tr
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'cursor-pointer border-t border-gray-100 transition-colors hover:bg-gray-50',
          actionBg
        )}
      >
        <td className="py-2.5 pl-3 pr-2">
          <div className="flex items-center gap-2">
            <ChevronDown
              className={cn(
                'h-3.5 w-3.5 shrink-0 text-gray-400 transition-transform',
                open && 'rotate-180'
              )}
            />
            <span className="text-sm font-medium text-gray-900">
              {result.test_name}
            </span>
          </div>
        </td>
        <td className="px-2 py-2.5 text-sm tabular-nums text-gray-900">
          {result.value}
        </td>
        <td className="px-2 py-2.5 text-sm text-gray-500">{result.unit}</td>
        <td className="hidden px-2 py-2.5 text-sm text-gray-500 sm:table-cell">
          {result.reference_range}
        </td>
        <td className="px-2 py-2.5">
          <StatusBadge status={result.status} />
        </td>
      </tr>
      {open && (
        <tr className={cn('border-t border-gray-100', actionBg)}>
          <td colSpan={5} className="px-3 pb-3 pt-0">
            <div className="rounded-lg bg-white/70 p-3 text-sm text-gray-600">
              <p className="sm:hidden mb-1.5 text-xs text-gray-400">
                Reference range: {result.reference_range}
              </p>
              <p className="leading-relaxed">{result.explanation}</p>
              {result.action_needed && (
                <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-amber-700">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Action may be needed — discuss this result with your doctor.
                </p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Main report
// ---------------------------------------------------------------------------

interface LabResultsReportProps {
  report: LabResultsResponse
  /** Raw inputs that produced the report — required for "Save to records". */
  inputs?: LabResultInput[]
  patientId?: string
  /** When true, hides Save/Share/Download actions (e.g. inside history view). */
  embedded?: boolean
  /** Stub banner — model not loaded, output is demo data. */
  isStub?: boolean
}

export default function LabResultsReport({
  report,
  inputs,
  patientId,
  embedded = false,
  isStub = false,
}: LabResultsReportProps) {
  const [labName, setLabName] = useState('')
  const [saved, setSaved] = useState(false)
  const save = useSaveLabResults()

  const hasCritical = report.critical_flags.length > 0

  function handleSave() {
    if (!patientId || !inputs) {
      toast.error('Cannot save — missing patient or result data.')
      return
    }
    save.mutate(
      {
        patientId,
        results: inputs,
        reportDate: new Date().toISOString().slice(0, 10),
        labName: labName.trim() || 'Lab report',
      },
      {
        onSuccess: () => {
          setSaved(true)
          toast.success('Saved to your records.')
        },
        onError: (err) =>
          toast.error(err.message || 'Could not save. Please try again.'),
      }
    )
  }

  async function handleShare() {
    const text = formatForSharing(report)
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text)
        toast.success('Summary copied — paste it to your doctor.')
      } else {
        throw new Error('Clipboard unavailable')
      }
    } catch {
      toast.error('Could not copy to clipboard on this device.')
    }
  }

  return (
    <div className="space-y-4">
      {/* Stub / demo banner */}
      {isStub && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            <span className="font-semibold">AI model not loaded — demo output.</span>{' '}
            These results are illustrative and must not be treated as a real
            interpretation.
          </p>
        </div>
      )}

      {/* Critical alerts banner */}
      {hasCritical && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <p className="text-sm font-semibold">
              Critical values detected — seek immediate medical attention.
            </p>
          </div>
          <ul className="mt-2 space-y-1 pl-7">
            {report.critical_flags.map((flag, i) => (
              <li
                key={i}
                className="list-disc text-sm text-red-700 marker:text-red-400"
              >
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Results table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 text-left text-[11px] font-medium uppercase tracking-wide text-gray-400">
              <th className="py-2.5 pl-3 pr-2">Test</th>
              <th className="px-2 py-2.5">Value</th>
              <th className="px-2 py-2.5">Unit</th>
              <th className="hidden px-2 py-2.5 sm:table-cell">Reference</th>
              <th className="px-2 py-2.5">Status</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((res, i) => (
              <ResultRow key={`${res.test_name}-${i}`} result={res} />
            ))}
          </tbody>
        </table>
        {report.results.length === 0 && (
          <p className="px-3 py-6 text-center text-sm text-gray-400">
            No results to display.
          </p>
        )}
      </div>

      {/* Summary */}
      {report.summary && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="mb-1.5 text-sm font-semibold text-gray-900">Summary</h3>
          <p className="text-sm leading-relaxed text-gray-600">{report.summary}</p>
        </div>
      )}

      {/* Patterns detected */}
      {report.patterns_detected.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            <Lightbulb className="h-4 w-4 text-teal-600" />
            Patterns detected
          </h3>
          <ul className="space-y-1.5">
            {report.patterns_detected.map((p, i) => (
              <li
                key={i}
                className="flex gap-2 text-sm leading-relaxed text-gray-600"
              >
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-teal-500" />
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Follow-up tests */}
      {report.follow_up_tests.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            <ClipboardList className="h-4 w-4 text-teal-600" />
            Suggested follow-up tests
          </h3>
          <ul className="space-y-2">
            {report.follow_up_tests.map((t, i) => (
              <li
                key={i}
                className="flex items-center justify-between gap-3 rounded-lg border border-gray-100 bg-gray-50/60 px-3 py-2"
              >
                <span className="text-sm text-gray-700">{t}</span>
                <span className="shrink-0 rounded-full bg-teal-50 px-2 py-0.5 text-[11px] font-medium text-teal-700">
                  Ask doctor about this
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer footer */}
      {report.disclaimer && (
        <p className="px-1 text-xs italic leading-relaxed text-gray-400">
          {report.disclaimer}
        </p>
      )}

      {/* Actions */}
      {!embedded && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Lab name (optional)
              </label>
              <input
                value={labName}
                onChange={(e) => setLabName(e.target.value)}
                placeholder="e.g. Apollo Diagnostics"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={handleSave}
                disabled={save.isPending || saved || !patientId || !inputs}
                className="bg-teal-600 hover:bg-teal-700"
              >
                {save.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Saving…
                  </>
                ) : saved ? (
                  <>
                    <CheckCircle2 className="h-4 w-4" /> Saved
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" /> Save to my records
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={handleShare}>
                <Copy className="h-4 w-4" /> Share with doctor
              </Button>
              <Button
                variant="outline"
                onClick={() => toast('Download PDF — coming soon')}
              >
                <Download className="h-4 w-4" /> Download PDF
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
