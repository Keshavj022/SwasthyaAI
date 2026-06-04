'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ShieldCheck, AlertTriangle, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuditLogs } from '@/hooks/useAudit'
import type { AuditLog } from '@/types'

/** The backend audit row carries more fields than the shared AuditLog type. */
interface AuditRow extends Partial<AuditLog> {
  audit_id?: string
  agent_name?: string
  escalation_triggered?: string | null
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

interface Props {
  /** Reports the count of active critical alerts so the page can wire its stat card. */
  onCountChange?: (count: number) => void
}

export default function CriticalAlerts({ onCountChange }: Props) {
  const router = useRouter()
  // Backend defaults to the last 24h. Filtering by the triage agent surfaces
  // emergency escalations specifically.
  const { data, isLoading, isError } = useAuditLogs({ agentType: 'triage', limit: 50 })

  const rows = (data?.logs ?? []) as AuditRow[]
  const alerts = rows.filter((r) => !!r.escalation_triggered)

  useEffect(() => {
    onCountChange?.(alerts.length)
  }, [alerts.length, onCountChange])

  if (isLoading) {
    return <Skeleton className="h-16 w-full rounded-xl" />
  }

  // Honest "all clear" state on error (e.g. endpoint unreachable / forbidden)
  // or when there are genuinely no escalations.
  if (isError || alerts.length === 0) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-green-50 border border-green-200">
        <ShieldCheck className="w-5 h-5 text-green-600 shrink-0" />
        <div>
          <p className="text-sm font-medium text-green-800">No critical alerts</p>
          <p className="text-xs text-green-600">
            No emergency triage escalations in the last 24 hours.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-red-50 border border-red-300 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-red-200">
        <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
        <p className="text-sm font-semibold text-red-800">
          {alerts.length} critical {alerts.length === 1 ? 'alert' : 'alerts'} (last 24h)
        </p>
      </div>
      <ul className="divide-y divide-red-100">
        {alerts.slice(0, 5).map((a, i) => (
          <li
            key={a.audit_id ?? i}
            className="flex items-center gap-3 px-4 py-2.5"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-red-900 truncate">
                {a.reasoning_summary || a.escalation_triggered || 'Emergency triage escalation'}
              </p>
              <p className="text-xs text-red-500">{timeAgo(a.timestamp)}</p>
            </div>
            <button
              onClick={() => router.push('/admin/audit')}
              className="shrink-0 flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-900 px-2 py-1 rounded-lg hover:bg-red-100 transition-colors"
            >
              View details <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
