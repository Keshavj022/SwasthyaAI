'use client'

import { useState } from 'react'
import { Loader2, FlaskConical, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import { orchestratorApi } from '@/lib/api'
import type { AgentResponse } from '@/types'

interface QueryRecord {
  id: string
  query: string
  response: AgentResponse
  timestamp: string
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
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await orchestratorApi.ask(
        `Clinical assessment — patient symptoms: ${input}`,
        undefined,
        { task: 'differential_diagnosis', symptoms: input }
      )
      setResult(res)
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          query: input,
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
          if (e.key === 'Enter' && e.metaKey) handleAnalyze()
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

      {error && (
        <p className="mt-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
      )}

      {result && (
        <div className="mt-4 p-4 rounded-xl bg-teal-50 border border-teal-100 space-y-2">
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {result.response}
          </p>
          {result.confidence > 0 && (
            <p className="text-xs text-teal-600 font-medium">
              Confidence: {Math.round(result.confidence * 100)}%
            </p>
          )}
          <div className="flex items-start gap-1.5 mt-2 p-2 bg-amber-50 rounded-lg border border-amber-100">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-700">
              {result.disclaimer || 'For clinical decision support only. Not a definitive diagnosis.'}
            </p>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium text-gray-500 mb-2">Recent queries</p>
          <div className="space-y-1.5">
            {history.map((h) => (
              <div key={h.id} className="rounded-xl border border-gray-100 overflow-hidden">
                <button
                  onClick={() =>
                    setExpandedId(expandedId === h.id ? null : h.id)
                  }
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
                  <div className="px-3 pb-3 text-xs text-gray-600 bg-gray-50 whitespace-pre-wrap leading-relaxed">
                    {h.response.response}
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
