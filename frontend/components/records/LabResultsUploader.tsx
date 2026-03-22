'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { useInterpretLab } from '@/hooks/useLabResults'
import type { LabResultsResponse, LabResultInput } from '@/types'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const KNOWN_TESTS = [
  { value: 'hemoglobin',        label: 'Hemoglobin',              unit: 'g/dL'     },
  { value: 'hba1c',             label: 'HbA1c',                   unit: '%'        },
  { value: 'fasting_glucose',   label: 'Fasting Glucose',         unit: 'mg/dL'    },
  { value: 'total_cholesterol', label: 'Total Cholesterol',       unit: 'mg/dL'    },
  { value: 'ldl',               label: 'LDL Cholesterol',         unit: 'mg/dL'    },
  { value: 'hdl',               label: 'HDL Cholesterol',         unit: 'mg/dL'    },
  { value: 'triglycerides',     label: 'Triglycerides',           unit: 'mg/dL'    },
  { value: 'creatinine',        label: 'Creatinine',              unit: 'mg/dL'    },
  { value: 'urea',              label: 'Urea (BUN)',              unit: 'mg/dL'    },
  { value: 'sgpt_alt',          label: 'SGPT/ALT',                unit: 'U/L'      },
  { value: 'sgot_ast',          label: 'SGOT/AST',                unit: 'U/L'      },
  { value: 'tsh',               label: 'TSH',                     unit: 'mIU/L'    },
  { value: 'wbc',               label: 'WBC',                     unit: '10^3/μL'  },
  { value: 'platelets',         label: 'Platelets',               unit: '10^3/μL'  },
  { value: 'sodium',            label: 'Sodium',                  unit: 'mEq/L'    },
  { value: 'potassium',         label: 'Potassium',               unit: 'mEq/L'    },
  { value: 'other',             label: 'Other (enter manually)',  unit: ''         },
]

const MAX_ROWS = 20

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RowState {
  id: string
  testKey: string
  customName: string
  value: string
  unit: string
  date: string
}

interface Props {
  patientId: string
  patientAge: number
  patientSex: 'male' | 'female' | 'other'
  onResults: (response: LabResultsResponse) => void
  onSubmit?: (inputs: LabResultInput[]) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeRow(): RowState {
  return {
    id: crypto.randomUUID(),
    testKey: '',
    customName: '',
    value: '',
    unit: '',
    date: '',
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LabResultsUploader({ patientId, patientAge, patientSex, onResults, onSubmit }: Props) {
  const [tab, setTab] = useState<'manual' | 'upload'>('manual')
  const [rows, setRows] = useState<RowState[]>([makeRow()])
  const [formError, setFormError] = useState<string | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadSubmitting, setUploadSubmitting] = useState(false)
  const [uploadInputKey, setUploadInputKey] = useState(0)

  const { mutate: interpretLab, isPending } = useInterpretLab()

  // ── Row helpers ──────────────────────────────────────────────────────────

  function addRow() {
    if (rows.length >= MAX_ROWS) return
    setRows((prev) => [...prev, makeRow()])
  }

  function removeRow(id: string) {
    setRows((prev) => prev.filter((r) => r.id !== id))
  }

  function updateRow(id: string, patch: Partial<RowState>) {
    setFormError(null)
    setRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, ...patch } : r))
    )
  }

  function handleTestKeyChange(id: string, testKey: string) {
    const knownTest = KNOWN_TESTS.find((t) => t.value === testKey)
    const unit = knownTest && testKey !== 'other' ? knownTest.unit : ''
    updateRow(id, { testKey, unit, customName: '' })
  }

  // ── Submit (manual) ──────────────────────────────────────────────────────

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)

    const validRows = rows.filter((r) => {
      const hasTest = r.testKey !== '' && (r.testKey !== 'other' || r.customName.trim() !== '')
      const numVal = parseFloat(r.value)
      return hasTest && !isNaN(numVal) && numVal >= 0
    })

    if (validRows.length === 0) {
      setFormError('Please enter a valid test name and value (0 or greater) for each row.')
      return
    }

    const results: LabResultInput[] = validRows.map((r) => ({
      testName: r.testKey === 'other' ? r.customName.trim() : r.testKey,
      value: parseFloat(r.value),
      unit: r.unit,
      date: r.date || undefined,
    }))

    onSubmit?.(results)

    interpretLab(
      { results, patientId, patientAge, patientSex },
      {
        onSuccess: (response) => {
          onResults(response)
        },
        onError: (err) => {
          toast.error(err.message ?? 'Failed to interpret lab results')
        },
      }
    )
  }

  // ── Upload tab ───────────────────────────────────────────────────────────

  async function handleUploadSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!uploadFile || uploadFile.type !== 'application/pdf') {
      toast.error('Please select a valid PDF file')
      return
    }
    setUploadSubmitting(true)
    try {
      // Stub — save to doctor review queue placeholder
      toast.success('PDF upload saves to doctor review queue')
      setUploadInputKey((k) => k + 1)
    } catch {
      toast.error('Failed to queue PDF for doctor review')
    } finally {
      setUploadSubmitting(false)
      setUploadFile(null)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
      {/* Tab bar */}
      <div className="flex gap-1 mb-5 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setTab('manual')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            tab === 'manual'
              ? 'bg-white border border-b-white border-gray-200 -mb-px text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Manual Entry
        </button>
        <button
          type="button"
          onClick={() => setTab('upload')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            tab === 'upload'
              ? 'bg-white border border-b-white border-gray-200 -mb-px text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload PDF
        </button>
      </div>

      {/* ── Manual Entry tab ── */}
      {tab === 'manual' && (
        <form onSubmit={handleSubmit} noValidate>
          {/* Column headers */}
          <div className="hidden sm:grid grid-cols-[1fr_120px_100px_130px_auto] gap-2 mb-1 px-1">
            <span className="text-xs font-medium text-gray-500">Test Name</span>
            <span className="text-xs font-medium text-gray-500">Value</span>
            <span className="text-xs font-medium text-gray-500">Unit</span>
            <span className="text-xs font-medium text-gray-500">Date</span>
            <span />
          </div>

          {/* Rows */}
          <div className="space-y-2">
            {rows.map((row) => (
              <div
                key={row.id}
                className="grid grid-cols-[1fr_120px_100px_130px_auto] gap-2 items-start"
              >
                {/* Test name column: may include custom name input */}
                <div className="flex flex-col gap-1">
                  <select
                    value={row.testKey}
                    onChange={(e) => handleTestKeyChange(row.id, e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select test…</option>
                    {KNOWN_TESTS.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  {row.testKey === 'other' && (
                    <input
                      type="text"
                      placeholder="Enter test name"
                      value={row.customName}
                      onChange={(e) => updateRow(row.id, { customName: e.target.value })}
                      className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  )}
                </div>

                {/* Value */}
                <input
                  type="number"
                  min="0"
                  step="any"
                  placeholder="0.0"
                  value={row.value}
                  onChange={(e) => updateRow(row.id, { value: e.target.value })}
                  className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                {/* Unit */}
                <input
                  type="text"
                  placeholder="Unit"
                  value={row.unit}
                  onChange={(e) => updateRow(row.id, { unit: e.target.value })}
                  className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                {/* Date */}
                <input
                  type="date"
                  value={row.date}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => updateRow(row.id, { date: e.target.value })}
                  className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                {/* Remove button */}
                {rows.length > 1 ? (
                  <button
                    type="button"
                    onClick={() => removeRow(row.id)}
                    aria-label="Remove row"
                    className="mt-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    ✕
                  </button>
                ) : (
                  <span className="w-5" />
                )}
              </div>
            ))}
          </div>

          {/* Add test + submit row */}
          <div className="flex items-center justify-between mt-4">
            <button
              type="button"
              onClick={addRow}
              disabled={rows.length >= MAX_ROWS}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
            >
              + Add test
            </button>

            <button
              type="submit"
              disabled={isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {isPending && (
                <svg
                  className="animate-spin h-4 w-4 text-white"
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
              )}
              Interpret Results
            </button>
          </div>

          {/* Error */}
          {formError && (
            <p className="text-red-600 text-sm mt-2">{formError}</p>
          )}
        </form>
      )}

      {/* ── Upload PDF tab ── */}
      {tab === 'upload' && (
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          <div>
            <label htmlFor="lab-pdf-upload" className="block text-sm font-medium text-gray-700 mb-1">
              Choose PDF file
            </label>
            <input
              key={uploadInputKey}
              id="lab-pdf-upload"
              type="file"
              accept=".pdf"
              onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
            />
          </div>
          {uploadFile && (
            <p className="text-xs text-gray-500">Selected: {uploadFile.name}</p>
          )}
          <button
            type="submit"
            disabled={uploadSubmitting || !uploadFile}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {uploadSubmitting && (
              <svg
                className="animate-spin h-4 w-4 text-white"
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
            )}
            Upload for Doctor Review
          </button>
        </form>
      )}
    </div>
  )
}
