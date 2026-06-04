'use client'

import { Fragment, useMemo, useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Download,
  Search,
  FileText,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { useAuditLogs, type AuditLogRow } from '@/hooks/useAudit'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 20

const AGENT_BADGE: Record<string, string> = {
  triage: 'bg-red-100 text-red-700',
  diagnostic_support: 'bg-blue-100 text-blue-700',
  communication: 'bg-teal-100 text-teal-700',
  health_support: 'bg-green-100 text-green-700',
  image_analysis: 'bg-purple-100 text-purple-700',
  voice: 'bg-orange-100 text-orange-700',
  drug_info: 'bg-cyan-100 text-cyan-700',
  health_memory: 'bg-violet-100 text-violet-700',
  lab_results: 'bg-yellow-100 text-yellow-700',
}

type ConfidenceFilter = 'all' | 'high' | 'medium' | 'low'

function prettyAgent(name: string | null | undefined): string {
  if (!name) return 'Unknown'
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function agentName(row: AuditLogRow): string {
  return row.agent_name ?? row.agentType ?? 'unknown'
}

function rowKey(row: AuditLogRow, i: number): string {
  return row.audit_id ?? row.id ?? `row-${i}`
}

function fmtTime(ts?: string): string {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return ts
  }
}

function inputSummary(row: AuditLogRow): string {
  if (row.inputSummary) return row.inputSummary
  if (row.action) return row.action
  if (row.escalation_triggered) return `Escalation: ${row.escalation_triggered}`
  if (row.reasoning_summary) {
    const first = row.reasoning_summary.split('.')[0]
    return first.length > 90 ? `${first.slice(0, 87)}...` : first
  }
  return 'AI interaction'
}

function isEmergency(row: AuditLogRow): boolean {
  const agent = agentName(row)
  const esc = (row.escalation_triggered ?? '').toLowerCase()
  return agent === 'triage' && (esc.includes('emergency') || esc.includes('critical'))
}

function isLowConfidence(row: AuditLogRow): boolean {
  return typeof row.confidence_score === 'number' && row.confidence_score < 40
}

export default function AuditLogTable() {
  const [agentFilter, setAgentFilter] = useState('all')
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceFilter>('all')
  const [userQuery, setUserQuery] = useState('')
  const [page, setPage] = useState(0)
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useAuditLogs({ limit: 500 })

  const allLogs = data?.logs ?? []

  const agentOptions = useMemo(() => {
    const set = new Set<string>()
    for (const log of allLogs) set.add(agentName(log))
    return Array.from(set).sort()
  }, [allLogs])

  const filtered = useMemo(() => {
    return allLogs.filter((log) => {
      if (agentFilter !== 'all' && agentName(log) !== agentFilter) return false

      if (confidenceFilter !== 'all') {
        const c = log.confidence_score
        if (typeof c !== 'number') return false
        if (confidenceFilter === 'high' && c < 80) return false
        if (confidenceFilter === 'medium' && (c < 40 || c >= 80)) return false
        if (confidenceFilter === 'low' && c >= 40) return false
      }

      if (userQuery.trim()) {
        const q = userQuery.trim().toLowerCase()
        const haystack = `${log.user ?? ''} ${log.userId ?? ''} ${log.audit_id ?? ''}`.toLowerCase()
        if (!haystack.includes(q)) return false
      }
      return true
    })
  }, [allLogs, agentFilter, confidenceFilter, userQuery])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount - 1)
  const visible = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE)

  const resetPage = () => setPage(0)

  function handleExport() {
    const headers = ['Timestamp', 'Agent', 'Input Summary', 'Confidence', 'Escalation', 'Reviewed']
    const rows = filtered.map((log) => [
      fmtTime(log.timestamp),
      prettyAgent(agentName(log)),
      inputSummary(log).replace(/"/g, '""'),
      log.confidence_score != null ? `${log.confidence_score}%` : 'N/A',
      log.escalation_triggered ?? '',
      log.reviewed ? 'Yes' : 'No',
    ])
    const csv = [headers, ...rows]
      .map((r) => r.map((cell) => `"${String(cell)}"`).join(','))
      .join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Agent</label>
            <select
              value={agentFilter}
              onChange={(e) => {
                setAgentFilter(e.target.value)
                resetPage()
              }}
              className="w-full h-9 rounded-md border border-gray-200 px-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
            >
              <option value="all">All agents</option>
              {agentOptions.map((a) => (
                <option key={a} value={a}>
                  {prettyAgent(a)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Confidence</label>
            <select
              value={confidenceFilter}
              onChange={(e) => {
                setConfidenceFilter(e.target.value as ConfidenceFilter)
                resetPage()
              }}
              className="w-full h-9 rounded-md border border-gray-200 px-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
            >
              <option value="all">All</option>
              <option value="high">High (≥80%)</option>
              <option value="medium">Medium (40–79%)</option>
              <option value="low">Low (&lt;40%)</option>
            </select>
          </div>

          <div className="lg:col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={userQuery}
                onChange={(e) => {
                  setUserQuery(e.target.value)
                  resetPage()
                }}
                placeholder="User ID or audit ID..."
                className="w-full h-9 rounded-md border border-gray-200 pl-8 pr-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
              />
            </div>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-gray-500">
            {isLoading ? 'Loading…' : `${filtered.length} entr${filtered.length === 1 ? 'y' : 'ies'}`}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isFetching && 'animate-spin')} /> Refresh
            </button>
            <button
              onClick={handleExport}
              disabled={filtered.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-red-50 border border-red-200" /> Emergency escalation
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-amber-50 border border-amber-200" /> Low confidence (&lt;40%)
        </span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-6">
            <div className="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 p-4">
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-800">Failed to load audit logs</p>
                <p className="mt-1 text-sm text-red-700">
                  {error?.message || 'The audit endpoint did not respond.'}
                </p>
                <button
                  onClick={() => refetch()}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Retry
                </button>
              </div>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-6 h-6" />}
            title="No audit entries"
            description="No log entries match the current filters."
            className="py-12"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr className="text-left text-xs font-semibold text-gray-500">
                  <th className="px-4 py-3 w-8" />
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Agent</th>
                  <th className="px-4 py-3">Input summary</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {visible.map((log, i) => {
                  const key = rowKey(log, safePage * PAGE_SIZE + i)
                  const open = expanded === key
                  const emergency = isEmergency(log)
                  const lowConf = isLowConfidence(log)
                  const agent = agentName(log)
                  return (
                    <Fragment key={key}>
                      <tr
                        onClick={() => setExpanded(open ? null : key)}
                        className={cn(
                          'cursor-pointer transition-colors',
                          emergency
                            ? 'bg-red-50 hover:bg-red-100'
                            : lowConf
                              ? 'bg-amber-50 hover:bg-amber-100'
                              : 'hover:bg-gray-50'
                        )}
                      >
                        <td className="px-4 py-3 text-gray-400">
                          {open ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {fmtTime(log.timestamp)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                              AGENT_BADGE[agent] ?? 'bg-gray-100 text-gray-700'
                            )}
                          >
                            {prettyAgent(agent)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-700 max-w-md truncate">
                          {inputSummary(log)}
                        </td>
                        <td className="px-4 py-3">
                          {typeof log.confidence_score === 'number' ? (
                            <span
                              className={cn(
                                'text-xs font-semibold',
                                log.confidence_score >= 80
                                  ? 'text-green-600'
                                  : log.confidence_score >= 40
                                    ? 'text-amber-600'
                                    : 'text-red-600'
                              )}
                            >
                              {log.confidence_score}%
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">N/A</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            {emergency && (
                              <span className="inline-flex items-center rounded-full bg-red-600 px-2 py-0.5 text-xs font-medium text-white">
                                Emergency
                              </span>
                            )}
                            {log.escalation_triggered && !emergency && (
                              <span className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                                Escalated
                              </span>
                            )}
                            {log.reviewed && (
                              <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                                Reviewed
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                      {open && (
                        <tr key={`${key}-detail`} className="bg-gray-50/60">
                          <td colSpan={6} className="px-12 py-4">
                            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
                              <Detail label="Audit ID" value={log.audit_id ?? log.id ?? '—'} mono />
                              <Detail
                                label="Explainability score"
                                value={
                                  typeof log.explainability_score === 'number'
                                    ? `${log.explainability_score}%`
                                    : '—'
                                }
                              />
                              <Detail
                                label="Escalation"
                                value={log.escalation_triggered ?? 'None'}
                              />
                              <Detail label="User" value={log.user ?? log.userId ?? '—'} mono />
                              <div className="md:col-span-2">
                                <dt className="text-xs font-medium text-gray-500 mb-1">
                                  Reasoning / output
                                </dt>
                                <dd className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                                  {log.reasoning_summary || log.outputSummary || 'No reasoning recorded.'}
                                </dd>
                              </div>
                            </dl>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-500">
            Page {safePage + 1} of {pageCount}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={safePage === 0}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              disabled={safePage >= pageCount - 1}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Detail({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 mb-0.5">{label}</dt>
      <dd className={cn('text-sm text-gray-800', mono && 'font-mono text-xs break-all')}>{value}</dd>
    </div>
  )
}
