'use client'

import { useMemo } from 'react'
import { Clock } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import type { Appointment } from '@/types'

const HOUR_START = 9
const HOUR_END = 18
const TOTAL_MINUTES = (HOUR_END - HOUR_START) * 60

const TYPE_COLORS: Record<string, string> = {
  consultation: 'bg-teal-100 border-teal-400 text-teal-800',
  'follow-up':  'bg-blue-100 border-blue-400 text-blue-800',
  emergency:    'bg-red-100 border-red-400 text-red-800',
  'check-up':   'bg-green-100 border-green-400 text-green-800',
}

function getColor(type: string) {
  return TYPE_COLORS[type?.toLowerCase()] ?? 'bg-gray-100 border-gray-400 text-gray-800'
}

function minutesFromStart(iso: string): number {
  const d = new Date(iso)
  return (d.getHours() - HOUR_START) * 60 + d.getMinutes()
}

function getCurrentMinutes(): number {
  const now = new Date()
  return (now.getHours() - HOUR_START) * 60 + now.getMinutes()
}

function isToday(iso: string): boolean {
  const d = new Date(iso)
  const now = new Date()
  return (
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear()
  )
}

interface Props {
  appointments: Appointment[]
  isLoading: boolean
  onSelect: (appt: Appointment) => void
}

export default function TodaySchedule({ appointments, isLoading, onSelect }: Props) {
  const todayAppts = useMemo(
    () =>
      appointments
        .filter((a) => a.status !== 'cancelled' && isToday(a.dateTime))
        .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime()),
    [appointments]
  )

  const currentMins = getCurrentMinutes()
  const nowPct = Math.max(0, Math.min(100, (currentMins / TOTAL_MINUTES) * 100))

  if (isLoading) {
    return <Skeleton className="h-28 w-full rounded-2xl" />
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <h2 className="text-base font-semibold text-gray-900 mb-4">Today&apos;s Schedule</h2>

      {todayAppts.length === 0 ? (
        <EmptyState
          icon={<Clock className="w-6 h-6" />}
          title="No appointments today"
          description="Your schedule is clear for today."
          className="py-6"
        />
      ) : (
        <div className="relative">
          {/* Hour labels */}
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            {Array.from({ length: HOUR_END - HOUR_START + 1 }, (_, i) => {
              const h = HOUR_START + i
              return (
                <span key={h} className="text-center" style={{ width: `${100 / (HOUR_END - HOUR_START)}%` }}>
                  {h <= 12 ? `${h}AM` : `${h - 12}PM`}
                </span>
              )
            })}
          </div>

          {/* Timeline bar */}
          <div className="relative h-16 bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
            {currentMins >= 0 && currentMins <= TOTAL_MINUTES && (
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-400 z-10"
                style={{ left: `${nowPct}%` }}
              />
            )}
            {todayAppts.map((appt) => {
              const startMin = minutesFromStart(appt.dateTime)
              const durationMin = 30
              const leftPct = (startMin / TOTAL_MINUTES) * 100
              const widthPct = (durationMin / TOTAL_MINUTES) * 100
              if (startMin < 0 || startMin > TOTAL_MINUTES) return null
              return (
                <button
                  key={appt.id}
                  onClick={() => onSelect(appt)}
                  title={`${appt.type} — ${new Date(appt.dateTime).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`}
                  className={`absolute top-1 bottom-1 rounded-md border text-xs font-medium px-1 truncate cursor-pointer hover:opacity-80 transition-opacity ${getColor(appt.type)}`}
                  style={{ left: `${leftPct}%`, width: `${Math.max(widthPct, 3)}%` }}
                >
                  {appt.type}
                </button>
              )
            })}
          </div>

          {/* List below timeline */}
          <div className="mt-3 space-y-1.5">
            {todayAppts.map((appt) => (
              <button
                key={appt.id}
                onClick={() => onSelect(appt)}
                className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-gray-50 transition-colors text-left"
              >
                <span className="w-2 h-2 rounded-full shrink-0 bg-teal-400" />
                <span className="text-xs text-gray-500 shrink-0 w-14">
                  {new Date(appt.dateTime).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-sm font-medium text-gray-900 flex-1 truncate">
                  {appt.patientId}
                </span>
                <span className={`ml-auto text-xs px-2 py-0.5 rounded-full capitalize ${getColor(appt.type)}`}>
                  {appt.type}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
