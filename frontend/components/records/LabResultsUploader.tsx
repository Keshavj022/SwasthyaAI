'use client'

import { useRef, useState } from 'react'
import { FlaskConical, Plus, Trash2, Upload, Loader2, FileText, X } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useInterpretLabResults } from '@/hooks/useLabResults'
import { documentApi } from '@/lib/api'
import type { LabResultInput, LabResultsResponse } from '@/types'

// ---------------------------------------------------------------------------
// Common tests catalogue (matches backend REFERENCE_RANGES keys) + auto units
// ---------------------------------------------------------------------------

export const COMMON_TESTS: { key: string; label: string; unit: string }[] = [
  { key: 'hemoglobin', label: 'Hemoglobin', unit: 'g/dL' },
  { key: 'hba1c', label: 'HbA1c', unit: '%' },
  { key: 'fasting_glucose', label: 'Fasting Glucose', unit: 'mg/dL' },
  { key: 'total_cholesterol', label: 'Total Cholesterol', unit: 'mg/dL' },
  { key: 'ldl', label: 'LDL Cholesterol', unit: 'mg/dL' },
  { key: 'hdl', label: 'HDL Cholesterol', unit: 'mg/dL' },
  { key: 'triglycerides', label: 'Triglycerides', unit: 'mg/dL' },
  { key: 'creatinine', label: 'Creatinine', unit: 'mg/dL' },
  { key: 'urea', label: 'Urea', unit: 'mg/dL' },
  { key: 'sgpt_alt', label: 'SGPT / ALT', unit: 'U/L' },
  { key: 'sgot_ast', label: 'SGOT / AST', unit: 'U/L' },
  { key: 'tsh', label: 'TSH', unit: 'mIU/L' },
  { key: 'wbc', label: 'WBC Count', unit: '10^3/μL' },
  { key: 'platelets', label: 'Platelets', unit: '10^3/μL' },
  { key: 'sodium', label: 'Sodium', unit: 'mEq/L' },
  { key: 'potassium', label: 'Potassium', unit: 'mEq/L' },
]

const MAX_ROWS = 20
const OTHER = '__other__'

interface FormRow {
  id: string
  testKey: string
  customName: string
  value: string
  unit: string
  date: string
}

function newRow(): FormRow {
  return {
    id: Math.random().toString(36).slice(2),
    testKey: '',
    customName: '',
    value: '',
    unit: '',
    date: new Date().toISOString().slice(0, 10),
  }
}

interface LabResultsUploaderProps {
  patientId: string
  patientAge: number
  patientSex: string
  onInterpreted: (response: LabResultsResponse, inputs: LabResultInput[]) => void
}

export default function LabResultsUploader({
  patientId,
  patientAge,
  patientSex,
  onInterpreted,
}: LabResultsUploaderProps) {
  const [method, setMethod] = useState<'manual' | 'pdf'>('manual')
  const [rows, setRows] = useState<FormRow[]>([newRow()])
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const interpret = useInterpretLabResults()

  // -- row helpers ---------------------------------------------------------

  function updateRow(id: string, patch: Partial<FormRow>) {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function handleTestChange(id: string, testKey: string) {
    const match = COMMON_TESTS.find((t) => t.key === testKey)
    updateRow(id, {
      testKey,
      unit: match ? match.unit : '',
      customName: testKey === OTHER ? '' : '',
    })
  }

  function addRow() {
    if (rows.length >= MAX_ROWS) {
      toast.error(`You can enter up to ${MAX_ROWS} tests at a time.`)
      return
    }
    setRows((prev) => [...prev, newRow()])
  }

  function removeRow(id: string) {
    setRows((prev) => (prev.length === 1 ? prev : prev.filter((r) => r.id !== id)))
  }

  // -- build payload -------------------------------------------------------

  function buildInputs(): LabResultInput[] | null {
    const inputs: LabResultInput[] = []
    for (const r of rows) {
      const name = r.testKey === OTHER ? r.customName.trim() : r.testKey
      if (!name && !r.value) continue // skip fully empty rows
      if (!name) {
        toast.error('Please select or name every test you have entered a value for.')
        return null
      }
      const numeric = parseFloat(r.value)
      if (r.value === '' || Number.isNaN(numeric)) {
        toast.error(`Enter a numeric value for "${name}".`)
        return null
      }
      inputs.push({ test_name: name, value: numeric, unit: r.unit.trim() })
    }
    if (inputs.length === 0) {
      toast.error('Add at least one test result.')
      return null
    }
    return inputs
  }

  function handleInterpret() {
    const inputs = buildInputs()
    if (!inputs) return
    interpret.mutate(
      { results: inputs, patientId, patientAge, patientSex },
      {
        onSuccess: (data) => onInterpreted(data, inputs),
        onError: (err) =>
          toast.error(err.message || 'Could not interpret results. Please try again.'),
      }
    )
  }

  // -- PDF upload ----------------------------------------------------------

  function handleFilePick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File is too large (max 10 MB).')
      return
    }
    setPdfFile(file)
  }

  async function handleUploadPdf() {
    if (!pdfFile) return
    setUploading(true)
    try {
      await documentApi.upload(patientId, pdfFile, {
        documentType: 'lab_report',
        title: pdfFile.name,
      })
      toast.success('Lab report uploaded. A doctor will review it shortly.')
      setPdfFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Upload failed. Please try again.'
      )
    } finally {
      setUploading(false)
    }
  }

  // -----------------------------------------------------------------------

  return (
    <div className="rounded-xl border border-gray-200 bg-white">
      {/* Method toggle */}
      <div className="flex gap-1 border-b border-gray-100 p-1.5">
        <button
          onClick={() => setMethod('manual')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-colors ${
            method === 'manual'
              ? 'bg-teal-50 text-teal-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <FlaskConical className="h-4 w-4" /> Enter values
        </button>
        <button
          onClick={() => setMethod('pdf')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-colors ${
            method === 'pdf'
              ? 'bg-teal-50 text-teal-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Upload className="h-4 w-4" /> Upload PDF
        </button>
      </div>

      {method === 'manual' ? (
        <div className="p-4 md:p-5">
          <p className="mb-3 text-xs text-gray-500">
            Add each test result from your lab report. We will explain what each
            value means in plain language.
          </p>

          {/* Column headings (desktop) */}
          <div className="mb-1.5 hidden grid-cols-[1fr_90px_90px_140px_36px] gap-2 px-1 text-[11px] font-medium uppercase tracking-wide text-gray-400 md:grid">
            <span>Test</span>
            <span>Value</span>
            <span>Unit</span>
            <span>Date</span>
            <span />
          </div>

          <div className="space-y-2.5">
            {rows.map((row) => (
              <div
                key={row.id}
                className="grid grid-cols-2 gap-2 rounded-lg border border-gray-100 bg-gray-50/60 p-2.5 md:grid-cols-[1fr_90px_90px_140px_36px] md:border-0 md:bg-transparent md:p-0"
              >
                {/* Test select (+ custom name when "Other") */}
                <div className="col-span-2 md:col-span-1">
                  <Select
                    value={row.testKey}
                    onValueChange={(v) => handleTestChange(row.id, v)}
                  >
                    <SelectTrigger className="bg-white">
                      <SelectValue placeholder="Select test" />
                    </SelectTrigger>
                    <SelectContent>
                      {COMMON_TESTS.map((t) => (
                        <SelectItem key={t.key} value={t.key}>
                          {t.label}
                        </SelectItem>
                      ))}
                      <SelectItem value={OTHER}>Other…</SelectItem>
                    </SelectContent>
                  </Select>
                  {row.testKey === OTHER && (
                    <Input
                      className="mt-2 bg-white"
                      placeholder="Test name"
                      value={row.customName}
                      onChange={(e) =>
                        updateRow(row.id, { customName: e.target.value })
                      }
                    />
                  )}
                </div>

                <Input
                  className="bg-white"
                  type="number"
                  inputMode="decimal"
                  step="any"
                  placeholder="Value"
                  value={row.value}
                  onChange={(e) => updateRow(row.id, { value: e.target.value })}
                />

                <Input
                  className="bg-white"
                  placeholder="Unit"
                  value={row.unit}
                  onChange={(e) => updateRow(row.id, { unit: e.target.value })}
                />

                <Input
                  className="bg-white"
                  type="date"
                  value={row.date}
                  onChange={(e) => updateRow(row.id, { date: e.target.value })}
                />

                <button
                  type="button"
                  onClick={() => removeRow(row.id)}
                  disabled={rows.length === 1}
                  aria-label="Remove test"
                  className="flex h-10 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-gray-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-3 flex items-center justify-between">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={addRow}
              disabled={rows.length >= MAX_ROWS}
              className="text-teal-700 hover:bg-teal-50 hover:text-teal-800"
            >
              <Plus className="h-4 w-4" /> Add test
            </Button>
            <span className="text-xs text-gray-400">
              {rows.length}/{MAX_ROWS}
            </span>
          </div>

          <Button
            type="button"
            onClick={handleInterpret}
            disabled={interpret.isPending}
            className="mt-4 w-full bg-teal-600 hover:bg-teal-700"
          >
            {interpret.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Interpreting…
              </>
            ) : (
              <>
                <FlaskConical className="h-4 w-4" /> Interpret results
              </>
            )}
          </Button>
        </div>
      ) : (
        <div className="p-4 md:p-5">
          <p className="mb-3 text-xs text-gray-500">
            Upload a PDF of your lab report. It will be securely stored for a
            doctor to review. Automatic extraction is not yet available.
          </p>

          {!pdfFile ? (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/60 py-10 text-center transition-colors hover:border-teal-300 hover:bg-teal-50/40"
            >
              <Upload className="h-7 w-7 text-gray-400" />
              <span className="text-sm font-medium text-gray-600">
                Click to choose a PDF
              </span>
              <span className="text-xs text-gray-400">PDF up to 10 MB</span>
            </button>
          ) : (
            <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-gray-900">
                  {pdfFile.name}
                </p>
                <p className="text-xs text-gray-400">
                  {(pdfFile.size / 1024).toFixed(0)} KB
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setPdfFile(null)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
                aria-label="Remove file"
                className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleFilePick}
          />

          <Button
            type="button"
            onClick={handleUploadPdf}
            disabled={!pdfFile || uploading}
            className="mt-4 w-full bg-teal-600 hover:bg-teal-700"
          >
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Uploading…
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" /> Upload report
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  )
}
