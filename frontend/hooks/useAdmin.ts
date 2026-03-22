'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import type { AdminUser, AdminStats, AdminAppointment } from '@/types'

export const adminKeys = {
  users: ['admin', 'users'] as const,
  stats: ['admin', 'stats'] as const,
  appointments: (params?: AdminAppointmentsParams) => ['admin', 'appointments', params] as const,
}

export function useAdminUsers() {
  return useQuery<AdminUser[], Error>({
    queryKey: adminKeys.users,
    queryFn: adminApi.listUsers,
  })
}

export function useCreateAdminUser() {
  const qc = useQueryClient()
  return useMutation<AdminUser, Error, { email: string; password: string; fullName: string; role: string }>({
    mutationFn: adminApi.createUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.users }),
  })
}

export function useUpdateAdminUser() {
  const qc = useQueryClient()
  return useMutation<AdminUser, Error, { userId: string; patch: { role?: string; isActive?: boolean } }>({
    mutationFn: ({ userId, patch }) => adminApi.updateUser(userId, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.users }),
  })
}

export function useResetAdminPassword() {
  return useMutation<{ tempPassword: string }, Error, string>({
    mutationFn: adminApi.resetPassword,
  })
}

export function useDeleteAdminUser() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.users }),
  })
}

export function useAdminStats() {
  return useQuery<AdminStats, Error>({
    queryKey: adminKeys.stats,
    queryFn: adminApi.getStats,
    refetchInterval: 30_000,
    staleTime: 15_000,
  })
}

export interface AdminAppointmentsParams {
  status?: string
  specialty?: string
  fromDate?: string
  toDate?: string
  limit?: number
  offset?: number
}

export function useAdminAppointments(params?: AdminAppointmentsParams) {
  return useQuery<{ total: number; appointments: AdminAppointment[] }, Error>({
    queryKey: adminKeys.appointments(params),
    queryFn: () => adminApi.listAppointments(params),
    staleTime: 30_000,
  })
}
