'use client'

import { useRouter } from 'next/navigation'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Pill,
  AlertTriangle,
  ExternalLink,
  MessageCircle,
  Droplet,
  CalendarClock,
} from 'lucide-react'
import { usePatient } from '@/hooks/usePatients'
import type { Appointment, Patient } from '@/types'

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

function resolveName(appt: Appointment, patient?: Patient): string {
  return appt.patientName || patient?.name || `Patient ${appt.patientId.slice(0, 6)}`
}

function resolveAge(appt: Appointment, patient?: Patient): number | undefined {
  return appt.patientAge ?? patient?.age
}

interface Props {
  appointment: Appointment | null
  open: boolean
  onClose: () => void
}

export default function PatientSheet({ appointment, open, onClose }: Props) {
  const router = useRouter()
  const patientId = appointment?.patientId ?? ''
  const { data: patient, isLoading } = usePatient(open && patientId ? patientId : '')

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        {appointment &&
          (() => {
            const name = resolveName(appointment, patient)
            const age = resolveAge(appointment, patient)
            const appointmentTime = new Date(appointment.dateTime).toLocaleString('en-IN', {
              weekday: 'short',
              day: 'numeric',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            })
            const allergies = patient?.allergies ?? []
            const medications = patient?.currentMedications ?? []
            const conditions = patient?.activeConditions ?? []
            const lastVisit = patient?.lastCheckIn

            return (
              <>
                <SheetHeader className="mb-6">
                  <SheetTitle className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-bold">
                      {initials(name)}
                    </div>
                    <div>
                      <p className="text-base font-semibold text-gray-900">{name}</p>
                      <p className="text-xs text-gray-500 font-normal">
                        {age != null ? `${age}y · ` : ''}
                        {appointmentTime}
                      </p>
                    </div>
                  </SheetTitle>
                </SheetHeader>

                <div className="space-y-5">
                  {/* Appointment */}
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Appointment
                    </h3>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-1 rounded-full bg-teal-50 text-teal-700 text-xs font-medium capitalize">
                        {appointment.type}
                      </span>
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                          appointment.status === 'confirmed'
                            ? 'bg-green-50 text-green-700'
                            : appointment.status === 'scheduled'
                            ? 'bg-blue-50 text-blue-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {appointment.status}
                      </span>
                    </div>
                    {(appointment.reason || appointment.notes) && (
                      <p className="mt-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-2.5">
                        {appointment.reason || appointment.notes}
                      </p>
                    )}
                  </section>

                  {/* Demographics */}
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Demographics
                    </h3>
                    {isLoading ? (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-4 w-40" />
                      </div>
                    ) : (
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <Droplet className="w-4 h-4 text-gray-400" />
                          <span>
                            Blood group:{' '}
                            <span className="font-medium text-gray-900">
                              {patient?.bloodGroup || 'Not recorded'}
                            </span>
                          </span>
                        </div>
                        {patient?.gender && (
                          <div className="flex items-center gap-2 pl-6 text-gray-500 capitalize">
                            {patient.gender}
                          </div>
                        )}
                      </div>
                    )}
                  </section>

                  {/* Allergies */}
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Allergies
                    </h3>
                    {isLoading ? (
                      <Skeleton className="h-6 w-48" />
                    ) : allergies.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {allergies.map((a) => (
                          <span
                            key={a}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-50 text-red-700 text-xs font-medium"
                          >
                            <AlertTriangle className="w-3 h-3" /> {a}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 italic">No known allergies on record</p>
                    )}
                  </section>

                  {/* Current medications */}
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Current Medications
                    </h3>
                    {isLoading ? (
                      <div className="space-y-1.5">
                        <Skeleton className="h-5 w-40" />
                        <Skeleton className="h-5 w-32" />
                      </div>
                    ) : medications.length > 0 ? (
                      <ul className="space-y-1.5">
                        {medications.map((m, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                            <Pill className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                            {m}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-400 italic">No active medications on record</p>
                    )}
                  </section>

                  {/* Active conditions */}
                  {(isLoading || conditions.length > 0) && (
                    <section>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Active Conditions
                      </h3>
                      {isLoading ? (
                        <Skeleton className="h-5 w-36" />
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {conditions.map((c) => (
                            <span
                              key={c}
                              className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </section>
                  )}

                  {/* Last visit */}
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Last Visit
                    </h3>
                    {isLoading ? (
                      <Skeleton className="h-4 w-44" />
                    ) : lastVisit ? (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <CalendarClock className="w-4 h-4 text-gray-400" />
                        {new Date(lastVisit).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 italic">No prior visit on record</p>
                    )}
                  </section>

                  {/* Actions */}
                  <section className="space-y-2 pt-2 border-t border-gray-100">
                    <button
                      onClick={() => {
                        onClose()
                        router.push(`/records?patientId=${encodeURIComponent(patientId)}`)
                      }}
                      className="flex items-center justify-between w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        <ExternalLink className="w-4 h-4" /> Open full record
                      </span>
                    </button>
                    <button
                      onClick={() => {
                        onClose()
                        router.push(`/chat?patientId=${encodeURIComponent(patientId)}`)
                      }}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition-colors"
                    >
                      <MessageCircle className="w-4 h-4" /> Start AI consultation
                    </button>
                  </section>
                </div>
              </>
            )
          })()}
      </SheetContent>
    </Sheet>
  )
}
