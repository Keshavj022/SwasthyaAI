'use client'

import { useState, KeyboardEvent } from 'react'
import { X, Loader2, Pill, AlertCircle } from 'lucide-react'
import { orchestratorApi } from '@/lib/api'

export default function DrugInteractionChecker() {
  const [drugs, setDrugs] = useState<string[]>([])
  const [inputVal, setInputVal] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState('')

  const addDrug = () => {
    const trimmed = inputVal.trim()
    if (trimmed && drugs.length < 5 && !drugs.includes(trimmed)) {
      setDrugs((prev) => [...prev, trimmed])
    }
    setInputVal('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addDrug()
    }
    if (e.key === 'Backspace' && !inputVal && drugs.length > 0) {
      setDrugs((prev) => prev.slice(0, -1))
    }
  }

  const removeDrug = (drug: string) =>
    setDrugs((prev) => prev.filter((d) => d !== drug))

  const handleCheck = async () => {
    if (drugs.length < 2 || loading) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await orchestratorApi.ask(
        `Check drug interactions for: ${drugs.join(', ')}`,
        undefined,
        { task: 'drug_interaction', medications: drugs }
      )
      setResult(res.response)
    } catch {
      setError('Failed to check interactions. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setDrugs([])
    setInputVal('')
    setResult(null)
    setError('')
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
          <Pill className="w-4 h-4 text-blue-600" />
        </div>
        <h2 className="text-base font-semibold text-gray-900">Drug Interaction Checker</h2>
      </div>

      <div className="flex flex-wrap gap-1.5 p-2 rounded-xl border border-gray-200 min-h-[44px] focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-transparent transition-all">
        {drugs.map((drug) => (
          <span
            key={drug}
            className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-medium"
          >
            {drug}
            <button
              type="button"
              onClick={() => removeDrug(drug)}
              className="hover:text-blue-900"
              aria-label={`Remove ${drug}`}
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        {drugs.length < 5 && (
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addDrug}
            placeholder={
              drugs.length === 0
                ? 'Type drug name and press Enter...'
                : 'Add another...'
            }
            className="flex-1 min-w-24 text-sm outline-none bg-transparent placeholder:text-gray-400"
          />
        )}
      </div>
      <p className="text-xs text-gray-400 mt-1">
        Add up to 5 drugs. Press Enter or comma to add.
      </p>

      <div className="flex gap-2 mt-3">
        <button
          onClick={handleCheck}
          disabled={drugs.length < 2 || loading}
          className="flex-1 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Checking...
            </>
          ) : (
            'Check Interactions'
          )}
        </button>
        {(drugs.length > 0 || result) && (
          <button
            onClick={handleClear}
            className="px-4 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {drugs.length === 1 && (
        <p className="mt-2 text-xs text-gray-500">
          Add at least 2 drugs to check interactions.
        </p>
      )}

      {error && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 rounded-xl border border-red-100">
          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <p className="text-xs text-red-700">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 rounded-xl bg-gray-50 border border-gray-200">
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {result}
          </p>
          <p className="mt-3 text-xs text-amber-600 italic">
            For clinical reference only. Always verify with current prescribing
            information.
          </p>
        </div>
      )}
    </div>
  )
}
