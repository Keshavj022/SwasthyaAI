'use client'

import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight, Calendar, CheckCircle, X } from 'lucide-react'
import { toast } from 'sonner'
import {
  startOfWeek, eachDayOfInterval, format, addWeeks, subWeeks,
  isToday as dateFnsIsToday, isSameDay,
} from 'date-fns'
import { useDoctorAppointments, useCancelAppointment } from '@/hooks/useAppointments'
import { useQueryClient } from '@tanstack/react-query'
import { AppointmentStatusBadge } from './AppointmentStatusBadge'
import { apiClient } from '@/lib/api'
import type { Appointment } from '@/types'

interface DoctorScheduleProps {
  doctorId: string
}

// Day names Mon-Sat
const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function AppointmentDetailCard({
  appt,
  doctorId,
  onClose,
}: {
  appt: Appointment
  doctorId: string
  onClose: () => void
}) {
  const qc = useQueryClient()
  const cancelMutation = useCancelAppointment()
  const [marking, setMarking] = useState(false)

  async function handleMarkComplete() {
    setMarking(true)
    try {
      await apiClient.patch(`/api/appointments/${appt.id}`, { status: 'completed' })
      qc.invalidateQueries({ queryKey: ['appointments', 'doctor', doctorId] })
      toast.success('Appointment marked as complete')
      onClose()
    } catch {
      toast.error('Failed to update appointment')
    } finally {
      setMarking(false)
    }
  }

  function handleCancel() {
    cancelMutation.mutate(
      { appointmentId: appt.id, patientId: appt.patientId },
      {
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: ['appointments', 'doctor', doctorId] })
          toast.success('Appointment cancelled')
          onClose()
        },
        onError: () => toast.error('Failed to cancel'),
      }
    )
  }

  return (
    <div className="absolute z-10 left-0 right-0 top-full mt-1 bg-white rounded-xl border border-gray-200 shadow-lg p-4 text-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-gray-900">Patient #{appt.patientId.slice(-6)}</p>
          <p className="text-xs text-gray-500">{formatTime(appt.dateTime)} · {appt.type}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X size={14} />
        </button>
      </div>
      {appt.notes && <p className="text-xs text-gray-500 bg-gray-50 rounded p-2 mb-3">{appt.notes}</p>}
      <AppointmentStatusBadge status={appt.status} />
      <div className="flex gap-2 mt-3">
        {appt.status !== 'completed' && (
          <button
            onClick={handleMarkComplete}
            disabled={marking}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg
                        bg-green-50 text-green-700 text-xs font-medium hover:bg-green-100 disabled:opacity-50"
          >
            <CheckCircle size={11} /> {marking ? 'Saving...' : 'Mark Complete'}
          </button>
        )}
        {appt.status !== 'cancelled' && appt.status !== 'completed' && (
          <button
            onClick={handleCancel}
            disabled={cancelMutation.isPending}
            className="flex-1 px-3 py-1.5 rounded-lg bg-red-50 text-red-600 text-xs font-medium
                        hover:bg-red-100 disabled:opacity-50"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

export function DoctorSchedule({ doctorId }: DoctorScheduleProps) {
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedApptId, setSelectedApptId] = useState<string | null>(null)

  const { data: appointments, isLoading } = useDoctorAppointments(doctorId)

  const baseWeek = useMemo(() => {
    const now = new Date()
    if (weekOffset > 0) return addWeeks(now, weekOffset)
    if (weekOffset < 0) return subWeeks(now, -weekOffset)
    return now
  }, [weekOffset])

  const weekDays = useMemo(() => {
    const start = startOfWeek(baseWeek, { weekStartsOn: 1 }) // Monday
    const end = new Date(start)
    end.setDate(start.getDate() + 5) // Monday to Saturday (6 days)
    return eachDayOfInterval({ start, end })
  }, [baseWeek])

  const weekLabel = `${format(weekDays[0], 'd MMM')} – ${format(weekDays[5], 'd MMM yyyy')}`

  function getApptsForDay(day: Date): Appointment[] {
    return (appointments ?? [])
      .filter((a) => isSameDay(new Date(a.dateTime), day) && a.status !== 'cancelled')
      .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
  }

  if (isLoading) {
    return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
  }

  return (
    <div>
      {/* Week navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setWeekOffset((w) => w - 1)}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ChevronLeft size={16} />
        </button>
        <div className="text-center">
          <p className="text-sm font-semibold text-gray-900">{weekLabel}</p>
          {weekOffset !== 0 && (
            <button
              onClick={() => setWeekOffset(0)}
              className="text-xs text-teal-600 hover:underline mt-0.5"
            >
              Today
            </button>
          )}
        </div>
        <button
          onClick={() => setWeekOffset((w) => w + 1)}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Week grid */}
      <div className="grid grid-cols-6 gap-2">
        {weekDays.map((day) => {
          const dayAppts = getApptsForDay(day)
          const isCurrentDay = dateFnsIsToday(day)

          return (
            <div key={day.toISOString()} className="min-h-[200px]">
              {/* Day header */}
              <div className={`text-center py-2 rounded-lg mb-2 ${
                isCurrentDay ? 'bg-teal-600 text-white' : 'bg-gray-100'
              }`}>
                <p className={`text-xs font-medium ${isCurrentDay ? 'text-teal-100' : 'text-gray-500'}`}>
                  {WEEK_DAYS[weekDays.indexOf(day)]}
                </p>
                <p className={`text-lg font-bold ${isCurrentDay ? 'text-white' : 'text-gray-900'}`}>
                  {format(day, 'd')}
                </p>
              </div>

              {/* Appointment cards */}
              <div className="space-y-1.5">
                {dayAppts.length === 0 ? (
                  <p className="text-xs text-gray-300 text-center py-4">—</p>
                ) : (
                  dayAppts.map((appt) => (
                    <div key={appt.id} className="relative">
                      <button
                        onClick={() =>
                          setSelectedApptId(selectedApptId === appt.id ? null : appt.id)
                        }
                        className={`w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors ${
                          appt.status === 'completed'
                            ? 'bg-gray-100 text-gray-500'
                            : appt.status === 'confirmed'
                            ? 'bg-green-50 text-green-800 border border-green-200'
                            : 'bg-teal-50 text-teal-800 border border-teal-200'
                        }`}
                      >
                        <p className="font-medium truncate">{formatTime(appt.dateTime)}</p>
                        <p className="text-[10px] truncate opacity-75">{appt.type}</p>
                      </button>

                      {selectedApptId === appt.id && (
                        <AppointmentDetailCard
                          appt={appt}
                          doctorId={doctorId}
                          onClose={() => setSelectedApptId(null)}
                        />
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty state for the whole week */}
      {(appointments ?? []).filter((a) =>
        weekDays.some((d) => isSameDay(new Date(a.dateTime), d))
      ).length === 0 && (
        <div className="text-center py-8">
          <Calendar size={32} className="mx-auto text-gray-300 mb-2" />
          <p className="text-sm text-gray-400">No appointments scheduled this week</p>
        </div>
      )}
    </div>
  )
}
