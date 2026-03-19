'use client'

import { useState } from 'react'
import { Calendar, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { useMyAppointments } from '@/hooks/useAppointments'
import { AppointmentStatusBadge } from './AppointmentStatusBadge'
import { CancelDialog } from './CancelDialog'
import type { Appointment } from '@/types'

interface PatientAppointmentListProps {
  patientId: string
  onReschedule: (appointment: Appointment) => void
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function isFuture(iso: string): boolean {
  return new Date(iso) > new Date()
}

export function PatientAppointmentList({ patientId, onReschedule }: PatientAppointmentListProps) {
  const { data: appointments, isLoading, isError } = useMyAppointments(patientId)
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null)
  const [showPast, setShowPast] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-600">Failed to load appointments. Please refresh.</p>
      </div>
    )
  }

  const all = appointments ?? []
  const upcoming = all
    .filter((a) => a.status !== 'cancelled' && a.status !== 'completed' && isFuture(a.dateTime))
    .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
  const past = all
    .filter((a) => a.status === 'completed' || !isFuture(a.dateTime))
    .sort((a, b) => new Date(b.dateTime).getTime() - new Date(a.dateTime).getTime())

  return (
    <div className="space-y-6">
      {/* Upcoming */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Upcoming ({upcoming.length})
        </h3>

        {upcoming.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center">
            <Calendar size={32} className="mx-auto text-gray-300 mb-2" />
            <p className="text-sm text-gray-400">No upcoming appointments</p>
          </div>
        ) : (
          <div className="space-y-3">
            {upcoming.map((appt) => (
              <div
                key={appt.id}
                className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-gray-900 truncate">
                        {appt.doctorName ?? 'Doctor TBD'}
                      </p>
                      <AppointmentStatusBadge status={appt.status} />
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-1">
                      <Calendar size={13} />
                      <span>{formatDateTime(appt.dateTime)}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-gray-500">
                      <Clock size={13} />
                      <span>Type: {appt.type} · 30 min</span>
                    </div>
                    {appt.notes && (
                      <p className="text-xs text-gray-400 mt-1 truncate">{appt.notes}</p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                  <button
                    onClick={() => onReschedule(appt)}
                    className="flex-1 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-medium
                                text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Reschedule
                  </button>
                  <button
                    onClick={() => setCancelTarget(appt)}
                    className="flex-1 px-3 py-1.5 rounded-lg border border-red-200 text-xs font-medium
                                text-red-600 hover:bg-red-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Past (collapsible) */}
      {past.length > 0 && (
        <section>
          <button
            onClick={() => setShowPast((v) => !v)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-gray-700 mb-3"
          >
            {showPast ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            Past appointments ({past.length})
          </button>

          {showPast && (
            <div className="space-y-3">
              {past.map((appt) => (
                <div
                  key={appt.id}
                  className="bg-gray-50 rounded-xl border border-gray-200 p-4 opacity-75"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-700 truncate">
                        {appt.doctorName ?? 'Doctor'}
                      </p>
                      <p className="text-xs text-gray-500">{formatDateTime(appt.dateTime)}</p>
                      <p className="text-xs text-gray-500">Type: {appt.type}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <AppointmentStatusBadge status={appt.status} />
                      {appt.notes && (
                        <p className="text-xs text-gray-500 mt-1 italic truncate max-w-[200px]" title={appt.notes}>
                          {appt.notes}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Cancel dialog */}
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
