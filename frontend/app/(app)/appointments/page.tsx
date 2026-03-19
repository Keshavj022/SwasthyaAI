'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { PatientAppointmentList } from '@/components/appointments/PatientAppointmentList'
import { BookingWizard } from '@/components/appointments/BookingWizard'
import { RescheduleDialog } from '@/components/appointments/RescheduleDialog'
import { DoctorSchedule } from '@/components/appointments/DoctorSchedule'
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
// Doctor view
// ---------------------------------------------------------------------------

function DoctorView({ userId }: { userId: string }) {
  const [tab, setTab] = useState(0)

  return (
    <>
      <TabBar tabs={['Schedule', 'Manage']} active={tab} onChange={setTab} />
      {tab === 0 ? (
        <DoctorSchedule doctorId={userId} />
      ) : (
        <div className="text-center py-12 text-sm text-gray-400">
          <p>Full appointment management coming soon.</p>
        </div>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function AppointmentsPageInner() {
  const { user } = useAuth()
  if (!user) return null

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-sm text-gray-500 mt-1">
            {user.role === 'doctor'
              ? 'Manage your schedule and patient appointments'
              : 'Book and manage your healthcare appointments'}
          </p>
        </div>

        {user.role === 'doctor' ? (
          <DoctorView userId={user.id} />
        ) : (
          <PatientView userId={user.id} />
        )}
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
