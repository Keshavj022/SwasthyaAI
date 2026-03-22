'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { documentApi } from '@/lib/api'
import type { UploadDocumentPayload } from '@/lib/api'
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

  const mutation = useMutation<MedicalDocument, Error, UploadDocumentPayload>({
    mutationFn: async (payload) => {
      setUploadProgress(0)
      // NOTE: This is simulated progress, not real upload progress.
      // For large files (e.g. DICOM, high-res scans), the interval will
      // reach 90% quickly and then jump to 100% on completion.
      // TODO: Wire up real Axios onUploadProgress in documentApi.upload for accurate tracking.
      const interval = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 20, 90))
      }, 200)
      try {
        const result = await documentApi.upload(payload)
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
