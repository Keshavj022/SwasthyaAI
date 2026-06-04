'use client'

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { auditApi } from '@/lib/api'
import type { AuditLog } from '@/types'

/**
 * The backend `/api/audit/logs` endpoint returns rich entries
 * (audit_id, agent_name, confidence_score, reasoning_summary, ...) rather than
 * the legacy `AuditLog` shape. We model both so the table can render whatever
 * the API actually sends without crashing.
 */
export interface AuditLogRow {
  // rich backend shape
  audit_id?: string
  agent_name?: string | null
  confidence_score?: number | null
  explainability_score?: number | null
  escalation_triggered?: string | null
  reasoning_summary?: string | null
  reviewed?: boolean
  timestamp?: string
  // legacy shape (kept for compatibility)
  id?: string
  action?: string
  agentType?: string
  userId?: string
  inputSummary?: string
  outputSummary?: string
  // duration if the backend ever provides it
  duration_ms?: number | null
  user?: string | null
}

interface AuditLogsParams {
  limit?: number
  offset?: number
  agentType?: string
}

export interface AuditLogsResult {
  logs: AuditLogRow[]
  total: number
}

export const auditKeys = {
  logs: (params?: AuditLogsParams) => ['audit', 'logs', params] as const,
}

export function useAuditLogs(params?: AuditLogsParams) {
  return useQuery<AuditLogsResult, Error>({
    queryKey: auditKeys.logs(params),
    // auditApi.getLogs returns { logs, total }; the runtime logs are AuditLogRow
    queryFn: () => auditApi.getLogs(params) as unknown as Promise<AuditLogsResult>,
    placeholderData: keepPreviousData,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// Re-export the legacy type for any consumers that import it from here.
export type { AuditLog }
