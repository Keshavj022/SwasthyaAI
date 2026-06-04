'use client'

import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/lib/api'
import type { SystemHealth } from '@/lib/api'
import type { AIModelStatus } from '@/types'

export interface AIStatusResult {
  models: AIModelStatus[]
  anyLoaded: boolean
}

export const healthKeys = {
  status: ['system', 'health'] as const,
  ping: ['system', 'ping'] as const,
  aiStatus: ['system', 'ai-status'] as const,
}

/** Backend `/api/health` — refreshes every 30s per spec. */
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

/** Local AI model status (MedGemma / MedSigLIP / MedASR): enabled / loaded / stub. */
export function useAIStatus() {
  return useQuery<AIStatusResult, Error>({
    queryKey: healthKeys.aiStatus,
    queryFn: healthApi.aiStatus,
    refetchInterval: 30_000,
    staleTime: 15_000,
  })
}
