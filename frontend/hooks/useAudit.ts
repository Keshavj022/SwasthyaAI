'use client'

import { useQuery } from '@tanstack/react-query'
import { auditApi } from '@/lib/api'
import type { AuditLog } from '@/types'

interface AuditLogsParams {
  limit?: number
  offset?: number
  agentType?: string
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
  })
}
