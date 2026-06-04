'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { labResultsApi } from '@/lib/api'
import type {
  LabResultInput,
  LabResultsResponse,
  SavedLabResultSet,
} from '@/types'

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const labResultKeys = {
  history: (patientId: string) => ['lab-results', 'history', patientId] as const,
}

// ---------------------------------------------------------------------------
// Interpret mutation — sends entered values to the lab-results agent
// ---------------------------------------------------------------------------

export interface InterpretVariables {
  results: LabResultInput[]
  patientId?: string
  patientAge: number
  patientSex: string
}

export function useInterpretLabResults() {
  return useMutation<LabResultsResponse, Error, InterpretVariables>({
    mutationFn: ({ results, patientId, patientAge, patientSex }) =>
      labResultsApi.interpret({
        results,
        patient_id: patientId,
        patient_age: patientAge,
        patient_sex: patientSex,
      }),
  })
}

// ---------------------------------------------------------------------------
// Save mutation — persists an interpreted set to the patient's records
// ---------------------------------------------------------------------------

export interface SaveVariables {
  patientId: string
  results: LabResultInput[]
  reportDate: string
  labName: string
}

export function useSaveLabResults() {
  const qc = useQueryClient()
  return useMutation<{ id: string; saved: boolean }, Error, SaveVariables>({
    mutationFn: ({ patientId, results, reportDate, labName }) =>
      labResultsApi.save({
        patient_id: patientId,
        results,
        report_date: reportDate,
        lab_name: labName,
      }),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: labResultKeys.history(patientId) })
    },
  })
}

// ---------------------------------------------------------------------------
// History query — previously saved lab result sets
// ---------------------------------------------------------------------------

export function useLabResultsHistory(patientId: string) {
  return useQuery<SavedLabResultSet[], Error>({
    queryKey: labResultKeys.history(patientId),
    queryFn: () => labResultsApi.getByPatient(patientId),
    enabled: !!patientId,
  })
}
