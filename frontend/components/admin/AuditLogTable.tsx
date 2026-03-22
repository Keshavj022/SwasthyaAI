'use client'

import React, { useState, useMemo } from 'react'
import { useAuditLogs, type AuditLogsParams } from '@/hooks/useAudit'
import { format, parseISO } from 'date-fns'
import { ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import type { AuditLog } from '@/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AGENT_COLORS: Record<string, string> = {
  triage: 'bg-red-100 text-red-700',
  health_memory: 'bg-blue-100 text-blue-700',
  medical_imaging: 'bg-purple-100 text-purple-700',
  prescription: 'bg-green-100 text-green-700',
  explainability: 'bg-yellow-100 text-yellow-700',
  orchestrator: 'bg-teal-100 text-teal-700',
}

function agentBadge(agent: string) {
  const cls = AGENT_COLORS[agent] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${cls}`}>
      {agent.replace(/_/g, ' ')}
    </span>
  )
}

function safeDate(raw: string) {
  try { return format(parseISO(raw), 'd MMM yyyy, HH:mm') } catch { return raw }
}

function confidenceBadge(score: number | null) {
  if (score === null) return <span className="text-gray-400 text-xs">—</span>
  const cls =
    score >= 80 ? 'text-teal-700 bg-teal-50' :
    score >= 50 ? 'text-yellow-700 bg-yellow-50' :
    'text-red-700 bg-red-50'
  return <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${cls}`}>{score}%</span>
}

function rowBackground(log: AuditLog): string {
  if (log.escalationTriggered) return 'bg-red-50 hover:bg-red-100'
  if (log.confidenceScore !== null && log.confidenceScore < 40) return 'bg-amber-50 hover:bg-amber-100'
  return 'hover:bg-gray-50'
}

function exportCsv(logs: AuditLog[]) {
  const headers = ['Timestamp', 'User', 'Agent', 'Input Summary', 'Confidence', 'Escalation', 'Reviewed']
  const rows = logs.map((l) => [
    l.timestamp,
    l.userId,
    l.agentType,
    `"${(l.inputSummary ?? '').replace(/"/g, '""')}"`,
    l.confidenceScore ?? '',
    l.escalationTriggered ?? '',
    l.reviewed ? 'yes' : 'no',
  ])
  const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

// ---------------------------------------------------------------------------
// Filter bar
// ---------------------------------------------------------------------------

const AGENTS = ['triage', 'health_memory', 'medical_imaging', 'prescription', 'explainability', 'orchestrator']

interface Filters {
  agentType: string
  fromDate: string
  toDate: string
  userId: string
  minConfidence: number | undefined
  escalationsOnly: boolean
}

function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  return (
    <div className="flex flex-wrap gap-2 items-end py-3 px-4 bg-gray-50 border-b border-gray-100">
      {/* Agent */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Agent</label>
        <select
          value={filters.agentType}
          onChange={(e) => onChange({ ...filters, agentType: e.target.value })}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
        >
          <option value="">All agents</option>
          {AGENTS.map((a) => (
            <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      {/* Date range */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">From</label>
        <input
          type="date"
          value={filters.fromDate}
          onChange={(e) => onChange({ ...filters, fromDate: e.target.value })}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">To</label>
        <input
          type="date"
          value={filters.toDate}
          onChange={(e) => onChange({ ...filters, toDate: e.target.value })}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
        />
      </div>

      {/* User search */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">User ID</label>
        <input
          type="text"
          value={filters.userId}
          placeholder="Search user…"
          onChange={(e) => onChange({ ...filters, userId: e.target.value })}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300 w-36"
        />
      </div>

      {/* Confidence */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Confidence</label>
        <select
          value={filters.minConfidence ?? ''}
          onChange={(e) => {
            const v = e.target.value
            onChange({ ...filters, minConfidence: v === '' ? undefined : Number(v) })
          }}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
        >
          <option value="">All</option>
          <option value="80">High (&gt;80%)</option>
          <option value="50">Medium (&gt;50%)</option>
        </select>
      </div>

      {/* Escalations only */}
      <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer mt-4">
        <input
          type="checkbox"
          checked={filters.escalationsOnly}
          onChange={(e) => onChange({ ...filters, escalationsOnly: e.target.checked })}
          className="rounded accent-teal-600"
        />
        Escalations only
      </label>

      {/* Reset */}
      <button
        type="button"
        onClick={() => onChange({ agentType: '', fromDate: '', toDate: '', userId: '', minConfidence: undefined, escalationsOnly: false })}
        className="mt-4 text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded border border-gray-200 bg-white"
      >
        Reset
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sortable header
// ---------------------------------------------------------------------------

type SortKey = 'timestamp' | 'agentType' | 'confidenceScore'

function SortHeader({
  label, col, sort, onSort,
}: {
  label: string
  col: SortKey
  sort: { key: SortKey; asc: boolean }
  onSort: (k: SortKey) => void
}) {
  const active = sort.key === col
  return (
    <button
      type="button"
      onClick={() => onSort(col)}
      className="flex items-center gap-1 font-semibold text-xs text-gray-500 uppercase tracking-wide hover:text-gray-700"
      aria-label={`Sort by ${label}`}
    >
      {label}
      {active ? (sort.asc ? <ChevronUp size={12} aria-hidden="true" /> : <ChevronDown size={12} aria-hidden="true" />) : null}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const PAGE_SIZE = 20

export function AuditLogTable() {
  const [page, setPage] = useState(0)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [sort, setSort] = useState<{ key: SortKey; asc: boolean }>({ key: 'timestamp', asc: false })
  const [filters, setFilters] = useState<Filters>({
    agentType: '',
    fromDate: '',
    toDate: '',
    userId: '',
    minConfidence: undefined,
    escalationsOnly: false,
  })

  const queryParams: AuditLogsParams = {
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    agentType: filters.agentType || undefined,
    fromDate: filters.fromDate || undefined,
    toDate: filters.toDate || undefined,
    userId: filters.userId || undefined,
    minConfidence: filters.minConfidence,
    escalationsOnly: filters.escalationsOnly || undefined,
    hours: !filters.fromDate && !filters.toDate ? 168 : undefined,
  }

  const { data, isLoading, error } = useAuditLogs(queryParams)

  const sorted = useMemo(() => {
    const logs = [...(data?.logs ?? [])]
    logs.sort((a, b) => {
      let cmp = 0
      if (sort.key === 'timestamp') cmp = a.timestamp.localeCompare(b.timestamp)
      if (sort.key === 'agentType') cmp = a.agentType.localeCompare(b.agentType)
      if (sort.key === 'confidenceScore') cmp = (a.confidenceScore ?? -1) - (b.confidenceScore ?? -1)
      return sort.asc ? cmp : -cmp
    })
    return logs
  }, [data?.logs, sort.key, sort.asc])

  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function handleSort(key: SortKey) {
    setSort((s) => ({ key, asc: s.key === key ? !s.asc : true }))
    setExpandedId(null)
  }

  function handleFiltersChange(f: Filters) {
    setFilters(f)
    setPage(0)
    setExpandedId(null)
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      {/* Filter bar */}
      <FilterBar filters={filters} onChange={handleFiltersChange} />

      {/* Export + pagination header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-white">
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {isLoading ? 'Loading…' : `${total.toLocaleString()} total entries`}
          </span>
          <span className="text-[10px] text-gray-400 italic">Column sort applies to current page</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => exportCsv(sorted)}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
          >
            <Download size={12} aria-hidden="true" />
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="p-1.5 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
            aria-label="Previous page"
          >
            <ChevronLeft size={14} aria-hidden="true" />
          </button>
          <span className="text-xs text-gray-500 w-20 text-center" aria-live="polite">
            {page + 1} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="p-1.5 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
            aria-label="Next page"
          >
            <ChevronRight size={14} aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table" aria-label="Audit logs">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="px-4 py-2 text-left">
                <SortHeader label="Timestamp" col="timestamp" sort={sort} onSort={handleSort} />
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">User</th>
              <th className="px-4 py-2 text-left">
                <SortHeader label="Agent" col="agentType" sort={sort} onSort={handleSort} />
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Input Summary</th>
              <th className="px-4 py-2 text-left">
                <SortHeader label="Confidence" col="confidenceScore" sort={sort} onSort={handleSort} />
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Flags</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">Loading audit logs…</td>
              </tr>
            )}
            {error && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-red-500 text-sm">Failed to load audit logs.</td>
              </tr>
            )}
            {!isLoading && !error && sorted.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">No audit logs match the current filters.</td>
              </tr>
            )}
            {sorted.map((log) => (
              <React.Fragment key={log.id}>
                <tr
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${rowBackground(log)}`}
                  onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                  data-expanded={expandedId === log.id}
                >
                  <td className="px-4 py-2.5 text-xs text-gray-600 whitespace-nowrap">{safeDate(log.timestamp)}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-500 max-w-[120px] truncate">{log.userId || '—'}</td>
                  <td className="px-4 py-2.5">{agentBadge(log.agentType)}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-600 max-w-[240px] truncate">{log.inputSummary || '—'}</td>
                  <td className="px-4 py-2.5">{confidenceBadge(log.confidenceScore)}</td>
                  <td className="px-4 py-2.5">
                    {log.escalationTriggered && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                        {log.escalationTriggered}
                      </span>
                    )}
                  </td>
                </tr>
                {expandedId === log.id && (
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <td colSpan={6} className="px-6 py-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                        <div>
                          <p className="font-semibold text-gray-700 mb-1">Full Input</p>
                          <p className="text-gray-600 whitespace-pre-wrap break-words">{log.inputSummary || '—'}</p>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-700 mb-1">Full Output</p>
                          <p className="text-gray-600 whitespace-pre-wrap break-words">{log.outputSummary || '—'}</p>
                        </div>
                        {log.reasoningSummary && (
                          <div className="md:col-span-2">
                            <p className="font-semibold text-gray-700 mb-1">Reasoning</p>
                            <p className="text-gray-600">{log.reasoningSummary}</p>
                          </div>
                        )}
                        <div className="md:col-span-2 flex gap-4 text-gray-500">
                          <span>Audit ID: <span className="font-mono">{log.auditId}</span></span>
                          <span>Reviewed: {log.reviewed ? 'Yes' : 'No'}</span>
                          {log.explainabilityScore !== null && (
                            <span>Explainability: {log.explainabilityScore}%</span>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
