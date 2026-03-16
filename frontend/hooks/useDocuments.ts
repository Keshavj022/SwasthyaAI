'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { documentApi } from '@/lib/api'
import type { MedicalDocument } from '@/types'

export const documentKeys = {
  byPatient: (patientId: string) => ['documents', 'patient', patientId] as const,
}

export function usePatientDocuments(patientId: string) {
  return useQuery<MedicalDocument[], Error>({
    queryKey: documentKeys.byPatient(patientId),
    queryFn: () => documentApi.getByPatient(patientId),
    enabled: !!patientId,
  })
}

export function useUploadDocument() {
  const qc = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)

  const mutation = useMutation<MedicalDocument, Error, { patientId: string; file: File }>({
    mutationFn: async ({ patientId, file }) => {
      setUploadProgress(0)
      // Simulate progress since axios FormData upload progress requires onUploadProgress config
      const interval = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 20, 90))
      }, 200)
      try {
        const result = await documentApi.upload(patientId, file)
        setUploadProgress(100)
        return result
      } finally {
        clearInterval(interval)
      }
    },
    onSuccess: (doc) => {
      qc.invalidateQueries({ queryKey: documentKeys.byPatient(doc.patientId) })
      setUploadProgress(0)
    },
    onError: () => setUploadProgress(0),
  })

  return { ...mutation, uploadProgress }
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation<{ success: boolean }, Error, { documentId: string; patientId: string }>({
    mutationFn: ({ documentId }) => documentApi.delete(documentId),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: documentKeys.byPatient(patientId) })
    },
  })
}
