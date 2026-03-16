'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { patientApi } from '@/lib/api'
import type { Patient, HealthCheckIn } from '@/types'

export const patientKeys = {
  all: ['patients'] as const,
  byId: (id: string) => ['patients', id] as const,
  healthHistory: (patientId: string) => ['patients', patientId, 'health-history'] as const,
}

export function usePatients() {
  return useQuery<Patient[], Error>({
    queryKey: patientKeys.all,
    queryFn: patientApi.getAll,
  })
}

export function usePatient(id: string) {
  return useQuery<Patient, Error>({
    queryKey: patientKeys.byId(id),
    queryFn: () => patientApi.getById(id),
    enabled: !!id,
  })
}

export function useCreatePatient() {
  const qc = useQueryClient()
  return useMutation<Patient, Error, Partial<Patient>>({
    mutationFn: patientApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: patientKeys.all }) },
  })
}

export function useUpdatePatient() {
  const qc = useQueryClient()
  return useMutation<Patient, Error, { id: string; data: Partial<Patient> }>({
    mutationFn: ({ id, data }) => patientApi.update(id, data),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: patientKeys.all })
      qc.invalidateQueries({ queryKey: patientKeys.byId(updated.id) })
    },
  })
}

export function useHealthHistory(patientId: string) {
  return useQuery<HealthCheckIn[], Error>({
    queryKey: patientKeys.healthHistory(patientId),
    queryFn: () => patientApi.getHealthHistory(patientId),
    enabled: !!patientId,
  })
}

export function useSubmitCheckIn() {
  const qc = useQueryClient()
  return useMutation<HealthCheckIn, Error, { patientId: string; data: Partial<HealthCheckIn> }>({
    mutationFn: ({ patientId, data }) => patientApi.submitCheckIn(patientId, data),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: patientKeys.healthHistory(patientId) })
    },
  })
}
