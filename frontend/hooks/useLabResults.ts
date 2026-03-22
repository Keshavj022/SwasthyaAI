'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { labResultsApi } from '@/lib/api'
import type { LabResultsResponse, SavedLabReport, LabResultInput } from '@/types'

export const labResultsKeys = {
  history: (patientId: string) => ['lab-results', 'history', patientId] as const,
}

export function useLabHistory(patientId: string) {
  return useQuery<SavedLabReport[], Error>({
    queryKey: labResultsKeys.history(patientId),
    queryFn: () => labResultsApi.getHistory(patientId),
    enabled: Boolean(patientId),
    staleTime: 30_000,
  })
}

export interface InterpretLabParams {
  results: LabResultInput[]
  patientId: string
  patientAge: number
  patientSex: 'male' | 'female' | 'other'
}

export function useInterpretLab() {
  return useMutation<LabResultsResponse, Error, InterpretLabParams>({
    mutationFn: labResultsApi.interpret,
  })
}

export interface SaveLabParams {
  patientId: string
  results: LabResultInput[]
  reportDate: string
  labName: string
  patientAge: number
  patientSex: 'male' | 'female' | 'other'
}

export function useSaveLab() {
  const qc = useQueryClient()
  return useMutation<{ id: string; saved: boolean }, Error, SaveLabParams>({
    mutationFn: labResultsApi.save,
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: labResultsKeys.history(variables.patientId) })
    },
  })
}
