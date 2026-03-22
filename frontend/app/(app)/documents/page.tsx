'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import * as Dialog from '@radix-ui/react-dialog'
import { Upload, X } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { DocumentGrid } from '@/components/documents/DocumentGrid'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentPreviewPanel } from '@/components/documents/DocumentPreviewPanel'
import type { MedicalDocument } from '@/types'

// ---------------------------------------------------------------------------
// Upload modal (wraps DocumentUpload in a Radix Dialog)
// ---------------------------------------------------------------------------

function UploadModal({
  patientId,
  onSuccess,
}: {
  patientId: string
  onSuccess: () => void
}) {
  const [open, setOpen] = useState(false)

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition-colors"
        >
          <Upload size={14} aria-hidden="true" /> Upload Document
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                     w-full max-w-lg bg-white rounded-2xl shadow-xl p-6 focus:outline-none
                     max-h-[90vh] overflow-y-auto"
        >
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Upload Medical Document
            </Dialog.Title>
            <Dialog.Close
              className="text-gray-400 hover:text-gray-600"
              aria-label="Close upload dialog"
            >
              <X size={18} aria-hidden="true" />
            </Dialog.Close>
          </div>
          <DocumentUpload
            patientId={patientId}
            onSuccess={() => {
              setOpen(false)
              onSuccess()
            }}
          />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

// ---------------------------------------------------------------------------
// Page inner (needs Suspense for useSearchParams)
// ---------------------------------------------------------------------------

function DocumentsPageInner() {
  const { user } = useAuth()
  const searchParams = useSearchParams()
  const [selectedDoc, setSelectedDoc] = useState<MedicalDocument | null>(null)
  const [gridKey, setGridKey] = useState(0)

  if (!user) return null

  // Doctors can view any patient's docs via ?patientId=xxx
  const queryPatientId = searchParams.get('patientId')
  const patientId = user.role === 'doctor' && queryPatientId
    ? queryPatientId
    : user.id

  const headerSubtitle = user.role === 'doctor' && queryPatientId
    ? `Viewing documents for Patient ID: ${queryPatientId}`
    : 'Your uploaded medical documents and records'

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Page header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
            <p className="text-sm text-gray-500 mt-1">{headerSubtitle}</p>
          </div>
          <UploadModal
            patientId={patientId}
            onSuccess={() => setGridKey((k) => k + 1)}
          />
        </div>

        {/* Split view: grid on left, preview panel on right */}
        <div className="flex gap-6 items-start">
          <div className={selectedDoc ? 'w-[55%]' : 'flex-1'}>
            <DocumentGrid
              key={gridKey}
              patientId={patientId}
              selectedId={selectedDoc?.id ?? null}
              onSelect={(doc) => setSelectedDoc(doc)}
            />
          </div>

          {selectedDoc && (
            <div className="w-[45%] sticky top-0" style={{ height: 'calc(100vh - 200px)' }}>
              <DocumentPreviewPanel
                doc={selectedDoc}
                onClose={() => setSelectedDoc(null)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function DocumentsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']}>
      <Suspense>
        <DocumentsPageInner />
      </Suspense>
    </ProtectedRoute>
  )
}
