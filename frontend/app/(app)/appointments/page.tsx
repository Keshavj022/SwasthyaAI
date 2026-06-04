'use client'

import { useState } from 'react'
import { Calendar, Clock, CalendarClock } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { PatientAppointmentList } from '@/components/appointments/PatientAppointmentList'
import { BookingWizard } from '@/components/appointments/BookingWizard'
import { RescheduleDialog } from '@/components/appointments/RescheduleDialog'
import { CancelDialog } from '@/components/appointments/CancelDialog'
import { DoctorSchedule } from '@/components/appointments/DoctorSchedule'
import { AppointmentStatusBadge } from '@/components/appointments/AppointmentStatusBadge'
import { useDoctorSchedule } from '@/hooks/useAppointments'
import type { Appointment } from '@/types'

// ---------------------------------------------------------------------------
// Tab bar
// ---------------------------------------------------------------------------

function TabBar({
  tabs,
  active,
  onChange,
}: {
  tabs: string[]
  active: number
  onChange: (i: number) => void
}) {
  return (
    <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6">
      {tabs.map((tab, i) => (
        <button
          key={tab}
          onClick={() => onChange(i)}
          className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
            active === i ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Patient view
// ---------------------------------------------------------------------------

function PatientView({ userId }: { userId: string }) {
  const [tab, setTab] = useState(0)
  const [rescheduleTarget, setRescheduleTarget] = useState<Appointment | null>(null)

  return (
    <>
      <TabBar tabs={['My Appointments', 'Book New']} active={tab} onChange={setTab} />

      {tab === 0 ? (
        <>
          <PatientAppointmentList
            patientId={userId}
            onReschedule={(appt) => setRescheduleTarget(appt)}
          />
          {rescheduleTarget && (
            <RescheduleDialog
              appointment={rescheduleTarget}
              open={!!rescheduleTarget}
              onOpenChange={(open) => { if (!open) setRescheduleTarget(null) }}
            />
          )}
        </>
      ) : (
        <BookingWizard
          patientId={userId}
          onSuccess={() => setTab(0)}
        />
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Doctor "Manage" tab — flat list of all appointments with quick actions
// ---------------------------------------------------------------------------

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function DoctorManageList({ doctorId }: { doctorId: string }) {
  const { data: appointments, isLoading, isError, refetch } = useDoctorSchedule(doctorId)
  const [rescheduleTarget, setRescheduleTarget] = useState<Appointment | null>(null)
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />)}
      </div>
    )
  }
  if (isError) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-600 mb-2">Failed to load appointments.</p>
        <button onClick={() => refetch()} className="text-xs text-teal-600 hover:underline">Try again</button>
      </div>
    )
  }

  const sorted = [...(appointments ?? [])].sort(
    (a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime()
  )
  const active = sorted.filter((a) => a.status !== 'cancelled' && a.status !== 'completed')

  if (active.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center">
        <Calendar size={32} className="mx-auto text-gray-300 mb-2" />
        <p className="text-sm text-gray-400">No active appointments to manage</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {active.map((appt) => (
        <div key={appt.id} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-semibold text-gray-900 truncate">
                  {appt.patientName ?? `Patient #${appt.patientId.slice(-6)}`}
                  {appt.patientAge != null && (
                    <span className="text-gray-400 font-normal"> · {appt.patientAge}y</span>
                  )}
                </p>
                <AppointmentStatusBadge status={appt.status} />
              </div>
              <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-1">
                <Calendar size={13} />
                <span>{formatDateTime(appt.dateTime)}</span>
              </div>
              <div className="flex items-center gap-1.5 text-sm text-gray-500">
                <Clock size={13} />
                <span>Type: {appt.type} · {appt.durationMinutes ?? 30} min</span>
              </div>
              {appt.notes && <p className="text-xs text-gray-400 mt-1 truncate">{appt.notes}</p>}
            </div>
          </div>
          <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={() => setRescheduleTarget(appt)}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <CalendarClock size={12} /> Reschedule
            </button>
            <button
              type="button"
              onClick={() => setCancelTarget(appt)}
              className="flex-1 px-3 py-1.5 rounded-lg border border-red-200 text-xs font-medium text-red-600 hover:bg-red-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ))}

      {rescheduleTarget && (
        <RescheduleDialog
          appointment={rescheduleTarget}
          open={!!rescheduleTarget}
          onOpenChange={(open) => { if (!open) setRescheduleTarget(null) }}
        />
      )}
      {cancelTarget && (
        <CancelDialog
          appointment={cancelTarget}
          open={!!cancelTarget}
          onOpenChange={(open) => { if (!open) setCancelTarget(null) }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Doctor view
// ---------------------------------------------------------------------------

function DoctorView({ userId }: { userId: string }) {
  const [tab, setTab] = useState(0)

  return (
    <>
      <TabBar tabs={['Schedule', 'Manage']} active={tab} onChange={setTab} />
      {tab === 0 ? <DoctorSchedule doctorId={userId} /> : <DoctorManageList doctorId={userId} />}
    </>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function AppointmentsPageInner() {
  const { user } = useAuth()
  if (!user) return null

  const isDoctor = user.role === 'doctor'

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className={isDoctor ? 'max-w-5xl mx-auto' : 'max-w-3xl mx-auto'}>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isDoctor
              ? 'Manage your schedule and patient appointments'
              : 'Book and manage your healthcare appointments'}
          </p>
        </div>

        {isDoctor ? <DoctorView userId={user.id} /> : <PatientView userId={user.id} />}
      </div>
    </div>
  )
}

export default function AppointmentsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']}>
      <AppointmentsPageInner />
    </ProtectedRoute>
  )
}
