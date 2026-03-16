'use client'

import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/lib/api'
import type { SystemHealth } from '@/lib/api'

export const healthKeys = {
  status: ['system', 'health'] as const,
  ping: ['system', 'ping'] as const,
}

export function useSystemHealth() {
  return useQuery<SystemHealth, Error>({
    queryKey: healthKeys.status,
    queryFn: healthApi.check,
    refetchInterval: 30_000, // refetch every 30 seconds
    staleTime: 15_000,
  })
}

export function useSystemPing() {
  return useQuery<{ status: string }, Error>({
    queryKey: healthKeys.ping,
    queryFn: healthApi.ping,
    refetchInterval: 30_000,
    staleTime: 15_000,
  })
}
