'use client'

import { useState } from 'react'
import { FlaskConical, History, ClipboardList, Stethoscope } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { usePatient, useHealthHistory } from '@/hooks/usePatients'
import { useMyAppointments } from '@/hooks/useAppointments'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import LabResultsUploader from '@/components/records/LabResultsUploader'
import LabResultsReport from '@/components/records/LabResultsReport'
import LabResultsHistory from '@/components/records/LabResultsHistory'
import type { LabResultInput, LabResultsResponse } from '@/types'

// ---------------------------------------------------------------------------
// Lab Results tab
// ---------------------------------------------------------------------------

function LabResultsTab({
  patientId,
  patientAge,
  patientSex,
}: {
  patientId: string
  patientAge: number
  patientSex: string
}) {
  const [report, setReport] = useState<LabResultsResponse | null>(null)
  const [inputs, setInputs] = useState<LabResultInput[]>([])
  const [isStub, setIsStub] = useState(false)

  function handleInterpreted(res: LabResultsResponse, used: LabResultInput[]) {
    setReport(res)
    setInputs(used)
    // The interpret endpoint returns the raw LabResultsResponse; a stub_mode
    // flag may be attached by the agent. Treat any truthy stub marker as demo.
    const stub = (res as unknown as Record<string, unknown>)['stub_mode']
    setIsStub(Boolean(stub))
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-5">
      <div className="lg:col-span-2">
        <LabResultsUploader
          patientId={patientId}
          patientAge={patientAge}
          patientSex={patientSex}
          onInterpreted={handleInterpreted}
        />
      </div>

      <div className="lg:col-span-3">
        {report ? (
          <LabResultsReport
            report={report}
            inputs={inputs}
            patientId={patientId}
            isStub={isStub}
          />
        ) : (
          <div className="flex h-full min-h-[260px] flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-white px-6 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-50 text-teal-600">
              <FlaskConical className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-gray-900">
              Your interpreted results will appear here
            </h3>
            <p className="mt-1 max-w-xs text-sm text-gray-500">
              Enter your lab values on the left and we will explain each result
              in plain language.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Visit History tab (simple list of past appointments)
// ---------------------------------------------------------------------------

function VisitHistoryTab({ patientId }: { patientId: string }) {
  const { data, isLoading, isError, error } = useMyAppointments(patientId)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error?.message || 'Could not load your visit history.'}
      </div>
    )
  }

  const visits = (data ?? [])
    .slice()
    .sort((a, b) => new Date(b.dateTime).getTime() - new Date(a.dateTime).getTime())

  if (visits.length === 0) {
    return (
      <EmptyState
        icon={<Stethoscope className="h-6 w-6" />}
        title="No visits recorded"
        description="Your past and upcoming appointments will be listed here."
      />
    )
  }

  return (
    <div className="space-y-3">
      {visits.map((v) => {
        const d = new Date(v.dateTime)
        return (
          <div
            key={v.id}
            className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4"
          >
            <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <span className="text-xs font-bold leading-none">
                {d.toLocaleDateString('en-IN', { day: '2-digit' })}
              </span>
              <span className="text-[10px] uppercase leading-none">
                {d.toLocaleDateString('en-IN', { month: 'short' })}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-gray-900">
                {v.doctorName || v.specialty || 'Consultation'}
              </p>
              <p className="truncate text-xs text-gray-500">
                {v.reason || v.type}
                {v.specialty ? ` · ${v.specialty}` : ''} ·{' '}
                {d.toLocaleTimeString('en-IN', {
                  hour: 'numeric',
                  minute: '2-digit',
                })}
              </p>
            </div>
            <span
              className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                v.status === 'completed'
                  ? 'bg-green-100 text-green-700'
                  : v.status === 'cancelled'
                    ? 'bg-gray-100 text-gray-500'
                    : 'bg-teal-100 text-teal-700'
              }`}
            >
              {v.status}
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function RecordsPage() {
  const { user } = useAuth()
  const patientId = user?.id ?? ''
  // Demographics drive sex/age-aware reference ranges. The patient record may
  // not load (doctor/admin viewing, or missing profile) — fall back sensibly.
  const { data: patient } = usePatient(patientId)
  // Touch health history so it's warm if other views need it (also validates id).
  useHealthHistory(patientId)

  if (!user) return null

  const patientAge = patient?.age ?? 35
  const patientSex = (patient?.gender ?? '').toLowerCase().startsWith('f')
    ? 'female'
    : 'male'

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mx-auto max-w-5xl">
        <PageHeader
          title="My Records"
          subtitle="Interpret your lab results and review your visit history"
        />

        <Tabs defaultValue="lab" className="w-full">
          <TabsList className="mb-5">
            <TabsTrigger value="lab" className="gap-1.5">
              <FlaskConical className="h-4 w-4" /> Lab Results
            </TabsTrigger>
            <TabsTrigger value="saved" className="gap-1.5">
              <ClipboardList className="h-4 w-4" /> Saved
            </TabsTrigger>
            <TabsTrigger value="visits" className="gap-1.5">
              <History className="h-4 w-4" /> Visit History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="lab">
            <LabResultsTab
              patientId={patientId}
              patientAge={patientAge}
              patientSex={patientSex}
            />
          </TabsContent>

          <TabsContent value="saved">
            <LabResultsHistory patientId={patientId} />
          </TabsContent>

          <TabsContent value="visits">
            <VisitHistoryTab patientId={patientId} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
