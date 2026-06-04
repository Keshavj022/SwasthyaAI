'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { documentApi, apiClient } from '@/lib/api'

// ---------------------------------------------------------------------------
// View-model
//
// The shared `MedicalDocument` type is intentionally minimal (a spine file we
// don't own). The backend list endpoint returns a richer record, so we
// normalise into a `DocumentVM` that the documents UI consumes directly.
//
// Backend list shape (GET /api/documents/patient/{id}):
//   { patient_id, total_documents, documents: [
//       { document_id, title, document_type, file_name, file_size,
//         mime_type, document_date, uploaded_at, tags, visit_id } ] }
// ---------------------------------------------------------------------------

export interface DocumentVM {
  id: string
  patientId: string
  title: string
  documentType: string
  fileName: string
  fileSize: number
  mimeType: string
  uploadedAt: string
  documentDate: string | null
  tags: string[]
}

interface BackendDocument {
  document_id: number | string
  title?: string
  document_type?: string
  file_name?: string
  file_size?: number
  mime_type?: string
  document_date?: string | null
  uploaded_at?: string
  tags?: string[] | null
}

function normalizeDocument(raw: BackendDocument, patientId: string): DocumentVM {
  return {
    id: String(raw.document_id),
    patientId,
    title: raw.title ?? raw.file_name ?? 'Untitled',
    documentType: raw.document_type ?? 'other',
    fileName: raw.file_name ?? 'document',
    fileSize: raw.file_size ?? 0,
    mimeType: raw.mime_type ?? 'application/octet-stream',
    uploadedAt: raw.uploaded_at ?? new Date().toISOString(),
    documentDate: raw.document_date ?? null,
    tags: Array.isArray(raw.tags) ? raw.tags : [],
  }
}

export const documentKeys = {
  byPatient: (patientId: string) => ['documents', 'patient', patientId] as const,
}

// ---------------------------------------------------------------------------
// List
// ---------------------------------------------------------------------------

export function usePatientDocuments(patientId: string) {
  return useQuery<DocumentVM[], Error>({
    queryKey: documentKeys.byPatient(patientId),
    queryFn: async () => {
      // documentApi.getByPatient returns the raw backend envelope.
      const raw = (await documentApi.getByPatient(patientId)) as unknown as {
        documents?: BackendDocument[]
      } | BackendDocument[]
      const list = Array.isArray(raw) ? raw : raw.documents ?? []
      return list.map((d) => normalizeDocument(d, patientId))
    },
    enabled: !!patientId,
  })
}

// ---------------------------------------------------------------------------
// Upload — real progress threaded through documentApi.upload onProgress
// ---------------------------------------------------------------------------

export interface UploadVars {
  patientId: string
  file: File
  documentType?: string
  title?: string
}

export function useUploadDocument() {
  const qc = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)

  const mutation = useMutation<unknown, Error, UploadVars>({
    mutationFn: async ({ patientId, file, documentType, title }) => {
      setUploadProgress(0)
      return documentApi.upload(
        patientId,
        file,
        { documentType, title },
        (percent) => setUploadProgress(percent)
      )
    },
    onSuccess: (_data, vars) => {
      setUploadProgress(100)
      qc.invalidateQueries({ queryKey: documentKeys.byPatient(vars.patientId) })
      // brief settle so the bar visibly reaches 100% before resetting
      setTimeout(() => setUploadProgress(0), 600)
    },
    onError: () => setUploadProgress(0),
  })

  const reset = useCallback(() => setUploadProgress(0), [])

  return { ...mutation, uploadProgress, resetProgress: reset }
}

// ---------------------------------------------------------------------------
// Delete
// ---------------------------------------------------------------------------

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation<{ success: boolean }, Error, { documentId: string; patientId: string }>({
    mutationFn: ({ documentId }) => documentApi.delete(documentId),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: documentKeys.byPatient(patientId) })
    },
  })
}

// ---------------------------------------------------------------------------
// Authenticated blob fetch — for inline preview.
//
// The download endpoint is auth-protected, so <img>/<iframe> src cannot carry
// the Bearer token. Fetch the bytes through the authenticated axios client and
// expose an object URL the viewer can render.
// ---------------------------------------------------------------------------

export function useDocumentBlobUrl(documentId: string | null, enabled: boolean) {
  return useQuery<{ objectUrl: string; mimeType: string }, Error>({
    queryKey: ['document-blob', documentId],
    queryFn: async () => {
      const { data, headers } = await apiClient.get(
        `/api/documents/${documentId}/download`,
        { responseType: 'blob' }
      )
      const blob = data as Blob
      const mimeType =
        (headers as Record<string, string>)['content-type'] ||
        blob.type ||
        'application/octet-stream'
      return { objectUrl: URL.createObjectURL(blob), mimeType }
    },
    enabled: enabled && !!documentId,
    staleTime: 5 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}
