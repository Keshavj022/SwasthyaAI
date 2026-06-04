'use client'

import { useState } from 'react'
import {
  Loader2,
  FlaskConical,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  ClipboardList,
} from 'lucide-react'
import { orchestratorApi } from '@/lib/api'
import type { DiagnosticDiagnosis, DiagnosticResponseData } from '@/lib/api'
import type { AgentResponse } from '@/types'
import StubBanner from './StubBanner'

interface QueryRecord {
  id: string
  query: string
  response: AgentResponse
  timestamp: string
}

/** Read the structured diagnostic payload off an AgentResponse (data preserved by the API). */
function diagData(res: AgentResponse | null): Partial<DiagnosticResponseData> | null {
  if (!res?.data) return null
  return res.data as Partial<DiagnosticResponseData>
}

function confidencePct(d: DiagnosticDiagnosis): number {
  // Backend confidence is 0–1; guard against accidental 0–100 values.
  const c = d.confidence > 1 ? d.confidence / 100 : d.confidence
  return Math.round(Math.max(0, Math.min(1, c)) * 100)
}

function DiagnosticResult({ res }: { res: AgentResponse }) {
  const data = diagData(res)
  const diffs = (data?.differential_diagnoses ?? []).slice(0, 3)
  const redFlags = data?.red_flags ?? []
  const workup = data?.recommended_workup ?? []
  const hasStructured = diffs.length > 0 || redFlags.length > 0 || workup.length > 0

  return (
    <div className="mt-4 space-y-3">
      {res.isStub && <StubBanner note={(res.data?.stub_note as string) || undefined} />}

      {res.emergency && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 border border-red-300 text-red-800">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <p className="text-xs font-semibold">
            Emergency features detected — escalate / seek urgent care.
          </p>
        </div>
      )}

      {/* Red flags — highlighted in red */}
      {redFlags.length > 0 && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200">
          <p className="text-xs font-semibold text-red-700 mb-1.5 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Red flags
          </p>
          <ul className="space-y-1">
            {redFlags.map((flag, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-red-700">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1 shrink-0" />
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Differential diagnoses with confidence % */}
      {diffs.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-500">Top differential diagnoses</p>
          {diffs.map((d) => {
            const pct = confidencePct(d)
            return (
              <div
                key={d.rank}
                className="p-3 rounded-xl bg-teal-50 border border-teal-100"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {d.rank}. {d.condition}
                  </p>
                  <span className="text-xs font-semibold text-teal-700 shrink-0">{pct}%</span>
                </div>
                <div className="mt-1.5 h-1.5 w-full rounded-full bg-teal-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-teal-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                {d.likelihood && (
                  <p className="text-xs text-gray-500 mt-1.5 capitalize">{d.likelihood}</p>
                )}
                {d.supporting_features && (
                  <p className="text-xs text-gray-600 mt-1">
                    <span className="font-medium text-gray-500">Supports: </span>
                    {d.supporting_features}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Recommended workup */}
      {workup.length > 0 && (
        <div className="p-3 rounded-xl bg-gray-50 border border-gray-200">
          <p className="text-xs font-semibold text-gray-600 mb-1.5 flex items-center gap-1.5">
            <ClipboardList className="w-3.5 h-3.5" /> Recommended workup
          </p>
          <ul className="space-y-1">
            {workup.map((w, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-gray-700">
                <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1 shrink-0" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Fallback: free-text response when no structured fields are present */}
      {!hasStructured && res.response && (
        <div className="p-3 rounded-xl bg-teal-50 border border-teal-100">
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {res.response}
          </p>
        </div>
      )}

      {/* Required disclaimer */}
      <div className="flex items-start gap-1.5 p-2.5 bg-amber-50 rounded-lg border border-amber-100">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-700">
          {res.disclaimer ||
            'For clinical decision support only. Not a definitive diagnosis.'}
        </p>
      </div>
    </div>
  )
}

export default function QuickDiagnosticTool() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AgentResponse | null>(null)
  const [history, setHistory] = useState<QueryRecord[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const handleAnalyze = async () => {
    if (!input.trim() || loading) return
    const symptomsText = input.trim()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await orchestratorApi.ask(
        `Clinical assessment — patient symptoms: ${symptomsText}`,
        undefined,
        {
          task: 'differential_diagnosis',
          // Pass both a structured list and the raw string for the agent.
          symptoms: symptomsText
            .split(/[,\n]/)
            .map((s) => s.trim())
            .filter(Boolean),
        }
      )
      setResult(res)
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          query: symptomsText,
          response: res,
          timestamp: new Date().toISOString(),
        },
        ...prev.slice(0, 4),
      ])
      setInput('')
    } catch {
      setError('Failed to analyze. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center">
          <FlaskConical className="w-4 h-4 text-teal-600" />
        </div>
        <h2 className="text-base font-semibold text-gray-900">Quick Diagnostic</h2>
      </div>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Describe patient symptoms, vitals, and relevant history..."
        rows={3}
        className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleAnalyze()
        }}
      />

      <button
        onClick={handleAnalyze}
        disabled={!input.trim() || loading}
        className="mt-2 w-full py-2 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Analyzing symptoms...
          </>
        ) : (
          'Analyze'
        )}
      </button>

      {loading && (
        <div className="mt-4 space-y-2 animate-pulse">
          <div className="h-3 w-1/3 rounded bg-gray-100" />
          <div className="h-16 w-full rounded-xl bg-gray-100" />
          <div className="h-16 w-full rounded-xl bg-gray-100" />
        </div>
      )}

      {error && (
        <p className="mt-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
      )}

      {result && !loading && <DiagnosticResult res={result} />}

      {history.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium text-gray-500 mb-2">Recent queries</p>
          <div className="space-y-1.5">
            {history.map((h) => (
              <div key={h.id} className="rounded-xl border border-gray-100 overflow-hidden">
                <button
                  onClick={() => setExpandedId(expandedId === h.id ? null : h.id)}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-gray-50 transition-colors"
                >
                  <span className="truncate text-gray-700 flex-1">{h.query}</span>
                  {expandedId === h.id ? (
                    <ChevronUp className="w-3.5 h-3.5 text-gray-400 ml-2 shrink-0" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-gray-400 ml-2 shrink-0" />
                  )}
                </button>
                {expandedId === h.id && (
                  <div className="px-3 pb-3 bg-gray-50">
                    <DiagnosticResult res={h.response} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
