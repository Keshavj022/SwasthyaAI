'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { UserCircle, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { usePatientLookup } from '@/hooks/usePatients'
import type { Appointment, Patient } from '@/types'
import { isToday } from '@/lib/utils'

function deriveStatus(iso: string): 'waiting' | 'in-progress' | 'completed' {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 0) return 'waiting'
  if (diff < 30 * 60 * 1000) return 'in-progress'
  return 'completed'
}

const STATUS_STYLE: Record<string, string> = {
  'waiting': 'bg-amber-50 text-amber-700',
  'in-progress': 'bg-blue-50 text-blue-700',
  'completed': 'bg-gray-100 text-gray-500',
}

const STATUS_LABEL: Record<string, string> = {
  'waiting': 'Waiting',
  'in-progress': 'In Progress',
  'completed': 'Completed',
}

/** Resolve a display name from the appointment, then the patient record, then a fallback. */
function displayName(appt: Appointment, patient?: Patient): string {
  return appt.patientName || patient?.name || `Patient ${appt.patientId.slice(0, 6)}`
}

function displayAge(appt: Appointment, patient?: Patient): number | undefined {
  return appt.patientAge ?? patient?.age
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

interface Props {
  appointments: Appointment[]
  isLoading: boolean
}

export default function PatientQueue({ appointments, isLoading }: Props) {
  const router = useRouter()
  const [sortBy, setSortBy] = useState<'time' | 'status'>('time')
  const { resolve } = usePatientLookup()

  const queue = useMemo(() => {
    const today = appointments.filter(
      (a) => a.status !== 'cancelled' && isToday(a.dateTime)
    )
    if (sortBy === 'time') {
      return [...today].sort(
        (a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime()
      )
    }
    const order: Record<string, number> = { 'in-progress': 0, 'waiting': 1, 'completed': 2 }
    return [...today].sort(
      (a, b) => (order[deriveStatus(a.dateTime)] ?? 3) - (order[deriveStatus(b.dateTime)] ?? 3)
    )
  }, [appointments, sortBy])

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
        <Skeleton className="h-5 w-32" />
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Patient Queue</h2>
        <div className="flex gap-1">
          {(['time', 'status'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors capitalize ${
                sortBy === s ? 'bg-teal-50 text-teal-700' : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {queue.length === 0 ? (
        <EmptyState
          icon={<UserCircle className="w-6 h-6" />}
          title="No patients today"
          description="No appointments scheduled for today."
          className="py-6"
        />
      ) : (
        <div className="space-y-2">
          {queue.map((appt) => {
            const status = deriveStatus(appt.dateTime)
            const patient = resolve(appt.patientId)
            const name = displayName(appt, patient)
            const age = displayAge(appt, patient)
            return (
              <div
                key={appt.id}
                className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="w-9 h-9 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-semibold text-sm shrink-0">
                  {initials(name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {name}
                    {age != null && (
                      <span className="text-gray-400 font-normal"> · {age}y</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {new Date(appt.dateTime).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {' · '}
                    <span className="capitalize">{appt.reason || appt.type}</span>
                  </p>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${STATUS_STYLE[status] ?? 'bg-gray-100 text-gray-500'}`}
                >
                  {STATUS_LABEL[status] ?? status}
                </span>
                <button
                  onClick={() => router.push(`/chat?patientId=${encodeURIComponent(appt.patientId)}`)}
                  className="shrink-0 flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-800 px-2 py-1 rounded-lg hover:bg-teal-50 transition-colors"
                  title="Start AI consultation with patient context"
                >
                  Start <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
