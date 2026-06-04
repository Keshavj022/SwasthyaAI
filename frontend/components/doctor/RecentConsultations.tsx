'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { Brain, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { useAuditLogs } from '@/hooks/useAudit'
import type { AuditLog } from '@/types'

/** Backend audit rows carry more fields than the shared AuditLog type. */
interface AuditRow extends Partial<AuditLog> {
  audit_id?: string
  agent_name?: string
  reasoning_summary?: string | null
  confidence_score?: number | null
}

function timeAgo(iso?: string): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

/** Audit confidence_score is 0–100 on the backend; normalise to a 0–1 fraction. */
function normConfidence(score?: number | null): number {
  if (score == null) return 0
  return score > 1 ? score / 100 : score
}

function confidenceBadge(fraction: number): string {
  if (fraction >= 0.8) return 'bg-green-50 text-green-700'
  if (fraction >= 0.5) return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-600'
}

export default function RecentConsultations() {
  const { data, isLoading, isError } = useAuditLogs({ limit: 5 })

  const records = useMemo(() => {
    const rows = (data?.logs ?? []) as AuditRow[]
    return rows.slice(0, 5).map((r, i) => ({
      id: r.audit_id ?? String(i),
      summary: r.reasoning_summary || 'AI-assisted consultation',
      agentUsed: r.agent_name || 'agent',
      confidence: normConfidence(r.confidence_score),
      timestamp: r.timestamp ?? '',
    }))
  }, [data])

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Recent AI Consultations</h2>
        <Link
          href="/admin/audit"
          className="text-xs text-teal-600 font-medium hover:underline flex items-center gap-0.5"
        >
          View log <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      ) : isError || records.length === 0 ? (
        <EmptyState
          icon={<Brain className="w-6 h-6" />}
          title="No recent consultations"
          description="AI-assisted consultations will appear here once logged."
          className="py-6"
        />
      ) : (
        <div className="space-y-2">
          {records.map((r) => (
            <div key={r.id} className="flex items-start gap-3 p-3 rounded-xl bg-gray-50">
              <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center shrink-0 mt-0.5">
                <Brain className="w-3.5 h-3.5 text-teal-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-800 truncate">{r.summary}</p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  {r.timestamp && (
                    <span className="text-xs text-gray-400">{timeAgo(r.timestamp)}</span>
                  )}
                  <span className="text-xs px-1.5 py-0.5 rounded bg-teal-50 text-teal-600 font-medium capitalize">
                    {r.agentUsed}
                  </span>
                  {r.confidence > 0 && (
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded font-medium ${confidenceBadge(r.confidence)}`}
                    >
                      {Math.round(r.confidence * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
