'use client'

import { useState, useMemo } from 'react'
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon, CheckCircle,
  X, CalendarClock, Ban, Loader2,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  startOfWeek, eachDayOfInterval, format, addWeeks, subWeeks,
  addDays, subDays, isToday as dateFnsIsToday, isSameDay,
} from 'date-fns'
import { useDoctorSchedule, useUpdateStatus } from '@/hooks/useAppointments'
import { AppointmentStatusBadge } from './AppointmentStatusBadge'
import { CancelDialog } from './CancelDialog'
import { RescheduleDialog } from './RescheduleDialog'
import type { Appointment } from '@/types'

interface DoctorScheduleProps {
  doctorId: string
}

const WEEK_DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
// Clinic hours 8 AM – 6 PM.
const HOURS = Array.from({ length: 10 }, (_, i) => 8 + i) // 8..17 (each row = 1h)

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function typeColor(appt: Appointment): string {
  if (appt.status === 'completed') return 'bg-gray-100 text-gray-500 border-gray-200'
  if (appt.status === 'cancelled') return 'bg-red-50 text-red-500 border-red-200 line-through'
  const t = (appt.type || '').toLowerCase()
  if (t.includes('emergency')) return 'bg-red-50 text-red-700 border-red-200'
  if (t.includes('follow')) return 'bg-amber-50 text-amber-800 border-amber-200'
  if (t.includes('lab')) return 'bg-purple-50 text-purple-800 border-purple-200'
  if (t.includes('vaccin')) return 'bg-blue-50 text-blue-800 border-blue-200'
  if (appt.status === 'confirmed') return 'bg-green-50 text-green-800 border-green-200'
  return 'bg-teal-50 text-teal-800 border-teal-200'
}

function patientLabel(appt: Appointment): string {
  const name = appt.patientName ?? `Patient #${appt.patientId.slice(-6)}`
  return appt.patientAge != null ? `${name} · ${appt.patientAge}y` : name
}

// ---------------------------------------------------------------------------
// Appointment detail popover (shared by week & day views)
// ---------------------------------------------------------------------------

function AppointmentDetail({
  appt,
  doctorId,
  onClose,
}: {
  appt: Appointment
  doctorId: string
  onClose: () => void
}) {
  const updateStatus = useUpdateStatus()
  const [cancelOpen, setCancelOpen] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)

  function handleMarkComplete() {
    updateStatus.mutate(
      { appointmentId: appt.id, status: 'completed', doctorId },
      {
        onSuccess: () => { toast.success('Appointment marked as complete'); onClose() },
        onError: (err) => toast.error(err.message || 'Failed to update appointment'),
      }
    )
  }

  const active = appt.status !== 'completed' && appt.status !== 'cancelled'

  return (
    <div
      className="absolute z-20 left-0 right-0 top-full mt-1 w-56 bg-white rounded-xl border border-gray-200 shadow-lg p-3 text-sm"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 truncate">
            {appt.patientName ?? `Patient #${appt.patientId.slice(-6)}`}
          </p>
          <p className="text-xs text-gray-500">
            {appt.patientAge != null ? `${appt.patientAge} yrs · ` : ''}{formatTime(appt.dateTime)}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 flex-shrink-0">
          <X size={14} />
        </button>
      </div>

      <p className="text-xs text-gray-600 mb-1">Type: <span className="font-medium">{appt.type}</span></p>
      {appt.notes && (
        <p className="text-xs text-gray-500 bg-gray-50 rounded p-2 mb-2 max-h-20 overflow-y-auto">{appt.notes}</p>
      )}
      <div className="mb-2"><AppointmentStatusBadge status={appt.status} /></div>

      {active && (
        <div className="space-y-1.5">
          <button
            type="button"
            onClick={handleMarkComplete}
            disabled={updateStatus.isPending}
            className="w-full flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg
                        bg-green-50 text-green-700 text-xs font-medium hover:bg-green-100 disabled:opacity-50"
          >
            {updateStatus.isPending ? <Loader2 size={11} className="animate-spin" /> : <CheckCircle size={11} />}
            Mark Complete
          </button>
          <button
            type="button"
            onClick={() => setRescheduleOpen(true)}
            className="w-full flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg
                        bg-gray-50 text-gray-700 text-xs font-medium hover:bg-gray-100"
          >
            <CalendarClock size={11} /> Reschedule
          </button>
          <button
            type="button"
            onClick={() => setCancelOpen(true)}
            className="w-full flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg
                        bg-red-50 text-red-600 text-xs font-medium hover:bg-red-100"
          >
            <X size={11} /> Cancel
          </button>
        </div>
      )}

      {cancelOpen && (
        <CancelDialog
          appointment={appt}
          open={cancelOpen}
          onOpenChange={setCancelOpen}
          onCancelled={onClose}
        />
      )}
      {rescheduleOpen && (
        <RescheduleDialog
          appointment={appt}
          open={rescheduleOpen}
          onOpenChange={setRescheduleOpen}
          onRescheduled={onClose}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Appointment block (clickable, opens popover)
// ---------------------------------------------------------------------------

function ApptBlock({
  appt,
  doctorId,
  expanded,
  onToggle,
  detailed,
}: {
  appt: Appointment
  doctorId: string
  expanded: boolean
  onToggle: () => void
  detailed?: boolean
}) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        className={`w-full text-left px-2 py-1 rounded-lg text-xs border transition-colors ${typeColor(appt)}`}
      >
        <p className="font-medium truncate">{formatTime(appt.dateTime)}</p>
        <p className="truncate text-[11px]">{patientLabel(appt)}</p>
        {detailed && <p className="truncate text-[10px] opacity-75">{appt.type}</p>}
      </button>
      {expanded && (
        <AppointmentDetail appt={appt} doctorId={doctorId} onClose={onToggle} />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main schedule
// ---------------------------------------------------------------------------

export function DoctorSchedule({ doctorId }: DoctorScheduleProps) {
  const [view, setView] = useState<'week' | 'day'>('week')
  const [anchor, setAnchor] = useState(() => new Date()) // week anchor / current day
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [breaks, setBreaks] = useState<string[]>([]) // ISO start times blocked locally

  const { data: appointments, isLoading, isError, refetch } = useDoctorSchedule(doctorId)

  const weekDays = useMemo(() => {
    const start = startOfWeek(anchor, { weekStartsOn: 1 }) // Monday
    return eachDayOfInterval({ start, end: addDays(start, 5) }) // Mon–Sat
  }, [anchor])

  const apptsByDay = useMemo(() => {
    const map = new Map<string, Appointment[]>()
    for (const a of appointments ?? []) {
      if (a.status === 'cancelled') continue
      const key = format(new Date(a.dateTime), 'yyyy-MM-dd')
      const arr = map.get(key) ?? []
      arr.push(a)
      map.set(key, arr)
    }
    for (const arr of map.values()) {
      arr.sort((x, y) => new Date(x.dateTime).getTime() - new Date(y.dateTime).getTime())
    }
    return map
  }, [appointments])

  function apptsForDay(day: Date): Appointment[] {
    return apptsByDay.get(format(day, 'yyyy-MM-dd')) ?? []
  }

  function apptsForHour(day: Date, hour: number): Appointment[] {
    return apptsForDay(day).filter((a) => new Date(a.dateTime).getHours() === hour)
  }

  function goToday() { setAnchor(new Date()) }
  function prev() { setAnchor((d) => (view === 'week' ? subWeeks(d, 1) : subDays(d, 1))) }
  function next() { setAnchor((d) => (view === 'week' ? addWeeks(d, 1) : addDays(d, 1))) }

  function toggleBreak(iso: string) {
    setBreaks((b) => (b.includes(iso) ? b.filter((x) => x !== iso) : [...b, iso]))
  }

  if (isLoading) {
    return <div className="h-72 bg-gray-100 rounded-xl animate-pulse" />
  }
  if (isError) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-600 mb-2">Failed to load your schedule.</p>
        <button onClick={() => refetch()} className="text-xs text-teal-600 hover:underline">Try again</button>
      </div>
    )
  }

  const weekLabel = `${format(weekDays[0], 'd MMM')} – ${format(weekDays[5], 'd MMM yyyy')}`
  const dayLabel = format(anchor, 'EEEE, d MMMM yyyy')

  return (
    <div onClick={() => setSelectedId(null)}>
      {/* Controls */}
      <div className="flex items-center justify-between mb-4 gap-2">
        <div className="flex items-center gap-1">
          <button onClick={prev} className="p-2 rounded-lg hover:bg-gray-100 text-gray-600" aria-label="Previous">
            <ChevronLeft size={16} />
          </button>
          <button onClick={next} className="p-2 rounded-lg hover:bg-gray-100 text-gray-600" aria-label="Next">
            <ChevronRight size={16} />
          </button>
          <button
            onClick={goToday}
            className="ml-1 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            Today
          </button>
        </div>

        <p className="text-sm font-semibold text-gray-900 text-center flex-1 truncate">
          {view === 'week' ? weekLabel : dayLabel}
        </p>

        {/* View toggle */}
        <div className="flex bg-gray-100 rounded-lg p-0.5">
          {(['week', 'day'] as const).map((v) => (
            <button
              key={v}
              onClick={(e) => { e.stopPropagation(); setView(v); setSelectedId(null) }}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                view === v ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* WEEK VIEW — time grid 8 AM–6 PM × Mon–Sat */}
      {view === 'week' && (
        <div className="overflow-x-auto">
          <div className="min-w-[640px]">
            {/* Day headers */}
            <div className="grid grid-cols-[48px_repeat(6,1fr)] gap-1 mb-1">
              <div />
              {weekDays.map((day, i) => {
                const isCurrent = dateFnsIsToday(day)
                return (
                  <div key={day.toISOString()} className={`text-center py-1.5 rounded-lg ${isCurrent ? 'bg-teal-600 text-white' : 'bg-gray-100'}`}>
                    <p className={`text-[10px] font-medium ${isCurrent ? 'text-teal-100' : 'text-gray-500'}`}>{WEEK_DAY_LABELS[i]}</p>
                    <p className={`text-sm font-bold ${isCurrent ? 'text-white' : 'text-gray-900'}`}>{format(day, 'd')}</p>
                  </div>
                )
              })}
            </div>

            {/* Hour rows */}
            <div className="space-y-1">
              {HOURS.map((hour) => (
                <div key={hour} className="grid grid-cols-[48px_repeat(6,1fr)] gap-1">
                  <div className="text-[10px] text-gray-400 text-right pr-1 pt-1">
                    {hour % 12 === 0 ? 12 : hour % 12}{hour < 12 ? 'a' : 'p'}
                  </div>
                  {weekDays.map((day) => {
                    const cellAppts = apptsForHour(day, hour)
                    return (
                      <div key={`${day.toISOString()}-${hour}`} className="min-h-[40px] bg-gray-50/60 rounded-md p-0.5 space-y-0.5">
                        {cellAppts.map((appt) => (
                          <div key={appt.id} onClick={(e) => e.stopPropagation()}>
                            <ApptBlock
                              appt={appt}
                              doctorId={doctorId}
                              expanded={selectedId === appt.id}
                              onToggle={() => setSelectedId(selectedId === appt.id ? null : appt.id)}
                            />
                          </div>
                        ))}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>

          {weekDays.every((d) => apptsForDay(d).length === 0) && (
            <div className="text-center py-8 mt-2">
              <CalendarIcon size={32} className="mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-400">No appointments scheduled this week</p>
            </div>
          )}
        </div>
      )}

      {/* DAY VIEW — single-day timeline with per-slot detail + Add break */}
      {view === 'day' && (
        <div className="space-y-1">
          {apptsForDay(anchor).length === 0 && breaks.length === 0 && (
            <div className="text-center py-8">
              <CalendarIcon size={32} className="mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-400">No appointments on this day</p>
            </div>
          )}
          {HOURS.map((hour) => {
            const slotDate = new Date(anchor)
            slotDate.setHours(hour, 0, 0, 0)
            const iso = slotDate.toISOString()
            const cellAppts = apptsForHour(anchor, hour)
            const isBreak = breaks.includes(iso)
            return (
              <div key={hour} className="flex gap-2 items-start border-b border-gray-100 py-1.5">
                <div className="w-14 flex-shrink-0 text-xs text-gray-400 pt-1">
                  {hour % 12 === 0 ? 12 : hour % 12}:00 {hour < 12 ? 'AM' : 'PM'}
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  {isBreak ? (
                    <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-gray-100 text-gray-500 text-xs">
                      <span className="flex items-center gap-1"><Ban size={11} /> Break — unavailable</span>
                      <button onClick={() => toggleBreak(iso)} className="text-gray-400 hover:text-gray-600">
                        <X size={12} />
                      </button>
                    </div>
                  ) : cellAppts.length > 0 ? (
                    cellAppts.map((appt) => (
                      <div key={appt.id} onClick={(e) => e.stopPropagation()}>
                        <ApptBlock
                          appt={appt}
                          doctorId={doctorId}
                          detailed
                          expanded={selectedId === appt.id}
                          onToggle={() => setSelectedId(selectedId === appt.id ? null : appt.id)}
                        />
                      </div>
                    ))
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleBreak(iso) }}
                      className="w-full text-left px-2 py-1.5 rounded-lg text-xs text-gray-300 hover:bg-gray-50 hover:text-gray-500"
                    >
                      + Add break
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
