'use client'

import { useState } from 'react'
import PageHeader from '@/components/ui/PageHeader'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/hooks/useAuth'
import LabResultsUploader from '@/components/records/LabResultsUploader'
import LabResultsReport from '@/components/records/LabResultsReport'
import LabResultsHistory from '@/components/records/LabResultsHistory'
import type { LabResultsResponse, LabResultInput } from '@/types'

// ---------------------------------------------------------------------------
// Inner client component
// ---------------------------------------------------------------------------

function RecordsPageInner() {
  const { user } = useAuth()
  const [tab, setTab] = useState<'lab' | 'visits'>('lab')
  const [labResponse, setLabResponse] = useState<LabResultsResponse | null>(null)
  const [labInputs, setLabInputs] = useState<LabResultInput[]>([])

  const patientId = user?.id ?? ''

  if (!patientId) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-gray-400">
        Loading your profile...
      </div>
    )
  }

  // TODO: Derive patientAge and patientSex from the patient profile once available.
  // Using defaults for now; these affect reference range interpretation.
  const patientAge = 30
  const patientSex: 'male' | 'female' | 'other' = 'other'

  return (
    <div>
      <PageHeader title="My Records" subtitle="Lab results and visit history" />

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setTab('lab')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            tab === 'lab'
              ? 'bg-white border border-b-white border-gray-200 -mb-px text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Lab Results
        </button>
        <button
          type="button"
          onClick={() => setTab('visits')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            tab === 'visits'
              ? 'bg-white border border-b-white border-gray-200 -mb-px text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Visit History
        </button>
      </div>

      {/* ── Lab Results tab ── */}
      {tab === 'lab' && (
        <div className="space-y-6">
          <LabResultsUploader
            patientId={patientId}
            patientAge={patientAge}
            patientSex={patientSex}
            onResults={(resp) => setLabResponse(resp)}
            onSubmit={(inputs) => setLabInputs(inputs)}
          />

          {labResponse && (
            <LabResultsReport
              response={labResponse}
              patientId={patientId}
              patientAge={patientAge}
              patientSex={patientSex}
              results={labInputs}
              onSaved={() => {
                // history refetches automatically via react-query
              }}
            />
          )}

          <LabResultsHistory
            patientId={patientId}
            patientAge={patientAge}
            patientSex={patientSex}
          />
        </div>
      )}

      {/* ── Visit History tab ── */}
      {tab === 'visits' && (
        <div className="rounded-xl border border-dashed p-12 text-center text-sm text-gray-400">
          Visit history coming soon
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page (server component wrapper with ProtectedRoute)
// ---------------------------------------------------------------------------

export default function RecordsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']}>
      <RecordsPageInner />
    </ProtectedRoute>
  )
}
