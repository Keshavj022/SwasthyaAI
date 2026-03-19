'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Calendar, Stethoscope, X, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { useMyAppointments, useCancelAppointment } from '@/hooks/useAppointments'
import type { Appointment } from '@/types'

const STATUS_BADGE: Record<string, string> = {
  scheduled: 'bg-blue-50 text-blue-700',
  confirmed: 'bg-green-50 text-green-700',
  pending: 'bg-amber-50 text-amber-700',
  completed: 'bg-gray-100 text-gray-500',
  cancelled: 'bg-red-50 text-red-500',
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface Props {
  patientId: string
}

export default function UpcomingAppointments({ patientId }: Props) {
  const { data: appointments, isLoading } = useMyAppointments(patientId)
  const cancel = useCancelAppointment()
  const [confirmId, setConfirmId] = useState<string | null>(null)

  const upcoming = (appointments ?? [])
    .filter((a) => a.status !== 'cancelled' && a.status !== 'completed')
    .filter((a) => new Date(a.dateTime) >= new Date())
    .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
    .slice(0, 3)

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
        <Skeleton className="h-5 w-40" />
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Upcoming Appointments</h2>
        <Link href="/appointments" className="text-xs text-teal-600 font-medium hover:underline flex items-center gap-0.5">
          View all <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {upcoming.length === 0 ? (
        <EmptyState
          icon={<Calendar className="w-6 h-6" />}
          title="No upcoming appointments"
          description="You don't have any scheduled appointments."
          action={{ label: 'Book now', onClick: () => window.location.href = '/appointments' }}
        />
      ) : (
        <div className="space-y-3">
          {upcoming.map((appt) => (
            <div
              key={appt.id}
              className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="w-9 h-9 rounded-lg bg-teal-100 flex items-center justify-center shrink-0">
                <Stethoscope className="w-4 h-4 text-teal-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {appt.doctorName ?? 'Doctor'}
                </p>
                <p className="text-xs text-gray-500">{formatDateTime(appt.dateTime)}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[appt.status] ?? 'bg-gray-100 text-gray-500'}`}>
                  {appt.status}
                </span>
                {confirmId === appt.id ? (
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        cancel.mutate({ appointmentId: appt.id, patientId })
                        setConfirmId(null)
                      }}
                      className="text-xs px-2 py-1 rounded bg-red-500 text-white hover:bg-red-600"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={() => setConfirmId(null)}
                      className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
                    >
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmId(appt.id)}
                    className="p-1 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                    title="Cancel appointment"
                    aria-label="Cancel appointment"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
