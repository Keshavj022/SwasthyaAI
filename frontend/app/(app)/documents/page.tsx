'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Upload, FolderOpen } from 'lucide-react'
import { toast } from 'sonner'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import {
  usePatientDocuments,
  useDeleteDocument,
  type DocumentVM,
} from '@/hooks/useDocuments'
import { apiClient } from '@/lib/api'
import { DocumentGrid } from '@/components/documents/DocumentGrid'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentPreviewPanel } from '@/components/documents/DocumentPreviewPanel'

function DocumentsInner() {
  const { user } = useAuth()
  const searchParams = useSearchParams()
  const isDoctor = user?.role === 'doctor'

  // Patients view their own docs (patient_id === user.id, per app convention).
  // Doctors arrive with ?patientId=xxx (e.g. from the consultation panel) and
  // may also enter one manually.
  const queryPatientId = searchParams.get('patientId') ?? undefined
  const ownPatientId = !isDoctor ? user?.id : undefined
  const [manualPatientId, setManualPatientId] = useState('')
  const patientId = queryPatientId ?? ownPatientId ?? manualPatientId

  const [search, setSearch] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [selected, setSelected] = useState<DocumentVM | null>(null)

  const { data: documents = [], isLoading, isError } = usePatientDocuments(patientId)
  const deleteMutation = useDeleteDocument()

  const patientLabel = isDoctor
    ? queryPatientId
      ? `Patient ${queryPatientId}`
      : patientId
        ? `Patient ${patientId}`
        : 'Select a patient'
    : user?.name ?? 'You'

  async function handleDownload(doc: DocumentVM) {
    try {
      const { data } = await apiClient.get(`/api/documents/${doc.id}/download`, {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(data as Blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.fileName
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch {
      toast.error('Download failed. Please try again.')
    }
  }

  function handleDelete(doc: DocumentVM) {
    deleteMutation.mutate(
      { documentId: doc.id, patientId: doc.patientId },
      {
        onSuccess: () => {
          toast.success('Document deleted')
          if (selected?.id === doc.id) setSelected(null)
        },
        onError: () => toast.error('Failed to delete document'),
      }
    )
  }

  // Doctor with no patient context yet → prompt for a patient id.
  const needsPatient = !patientId

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-3 px-4 md:px-6 py-3 border-b border-gray-200 bg-white flex-wrap">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Documents</h1>
          <p className="text-xs text-gray-500">
            {isDoctor ? patientLabel : 'Your medical documents and reports'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents…"
            className="h-9 w-44 md:w-56"
          />
          <Button onClick={() => setUploadOpen(true)} disabled={needsPatient} className="h-9">
            <Upload size={15} className="mr-1.5" /> Upload
          </Button>
        </div>
      </div>

      {needsPatient ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-sm">
            <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center text-gray-400 mb-4 mx-auto">
              <FolderOpen className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">Select a patient</h3>
            <p className="text-sm text-gray-500 mb-4">
              Enter a patient ID to view their documents, or open this page from a consultation.
            </p>
            <div className="flex items-center gap-2">
              <Input
                value={manualPatientId}
                onChange={(e) => setManualPatientId(e.target.value)}
                placeholder="Patient ID (e.g. P12345)"
                className="h-9"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex min-h-0">
          {/* Grid */}
          <div className="flex-1 min-w-0 p-4 md:p-6 flex flex-col min-h-0">
            <DocumentGrid
              documents={documents}
              isLoading={isLoading}
              isError={isError}
              selectedId={selected?.id}
              searchTerm={search}
              onSelect={setSelected}
              onDownload={handleDownload}
              onDelete={handleDelete}
              onUploadClick={() => setUploadOpen(true)}
            />
          </div>

          {/* Preview panel — empty-state on lg, full panel once a doc is picked */}
          <DocumentPreviewPanel
            doc={selected}
            patientLabel={patientLabel}
            onClose={() => setSelected(null)}
            onDownload={handleDownload}
            onDelete={handleDelete}
          />
        </div>
      )}

      {/* Upload dialog */}
      {patientId && (
        <DocumentUpload
          open={uploadOpen}
          onOpenChange={setUploadOpen}
          patientId={patientId}
          patientLabel={patientLabel}
        />
      )}
    </div>
  )
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']}>
      <Suspense>
        <DocumentsInner />
      </Suspense>
    </ProtectedRoute>
  )
}
