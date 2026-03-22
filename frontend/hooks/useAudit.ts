'use client'

import { useQuery } from '@tanstack/react-query'
import { auditApi } from '@/lib/api'
import type { AuditLog } from '@/types'

export interface AuditLogsParams {
  limit?: number
  offset?: number
  agentType?: string
  userId?: string
  minConfidence?: number
  escalationsOnly?: boolean
  fromDate?: string
  toDate?: string
  hours?: number
}

interface AuditLogsResult {
  logs: AuditLog[]
  total: number
}

export const auditKeys = {
  logs: (params?: AuditLogsParams) => ['audit', 'logs', params] as const,
}

export function useAuditLogs(params?: AuditLogsParams) {
  return useQuery<AuditLogsResult, Error>({
    queryKey: auditKeys.logs(params),
    queryFn: () => auditApi.getLogs(params),
    staleTime: 30_000,
  })
}
