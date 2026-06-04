'use client'

import { useQuery } from '@tanstack/react-query'
import { patientApi } from '@/lib/api'
import { differenceInYears, parseISO } from 'date-fns'
import type { Patient, HealthCheckIn } from '@/types'

interface PatientContextPanelProps {
  patientId: string
}

function computeAge(patient: Patient): string {
  if (typeof patient.age === 'number') return `${patient.age} yrs`
  if (patient.dateOfBirth) {
    try {
      return `${differenceInYears(new Date(), parseISO(patient.dateOfBirth))} yrs`
    } catch {
      /* fall through */
    }
  }
  return 'Unknown'
}

export function PatientContextPanel({ patientId }: PatientContextPanelProps) {
  const { data: patient, isLoading, isError } = useQuery<Patient>({
    queryKey: ['patient', patientId],
    queryFn: () => patientApi.getById(patientId),
    enabled: !!patientId,
  })

  const { data: checkIns } = useQuery<HealthCheckIn[]>({
    queryKey: ['health-history', patientId],
    queryFn: () => patientApi.getHealthHistory(patientId),
    enabled: !!patientId,
  })

  if (isLoading) {
    return (
      <aside className="w-52 border-l border-gray-200 bg-white p-4 flex flex-col gap-3">
        <div className="h-4 bg-gray-100 rounded animate-pulse w-2/3" />
        <div className="h-3 bg-gray-100 rounded animate-pulse w-full" />
        <div className="h-3 bg-gray-100 rounded animate-pulse w-3/4" />
      </aside>
    )
  }

  if (isError || !patient) {
    return (
      <aside className="w-52 border-l border-gray-200 bg-white p-4">
        <p className="text-xs text-red-500">Failed to load patient context.</p>
      </aside>
    )
  }

  const latestCheckIn = checkIns?.[0]
  const conditions = patient.activeConditions ?? []
  const medications = patient.currentMedications ?? []

  return (
    <aside className="w-52 border-l border-gray-200 bg-white flex flex-col overflow-y-auto">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Patient Context</p>
      </div>

      <div className="px-4 py-3 flex flex-col gap-3 text-xs">
        {/* Name */}
        {patient.name ? (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Name</p>
            <p className="text-gray-900 font-medium">{patient.name}</p>
          </div>
        ) : (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">ID</p>
            <p className="text-gray-700 font-mono text-[10px] truncate">{patient.id}</p>
          </div>
        )}

        {/* Age + gender */}
        <div className="flex gap-4">
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Age</p>
            <p className="text-gray-700">{computeAge(patient)}</p>
          </div>
          {patient.gender && (
            <div>
              <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Sex</p>
              <p className="text-gray-700 capitalize">{patient.gender}</p>
            </div>
          )}
        </div>

        {patient.bloodGroup && (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Blood Group</p>
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-red-50 text-red-700 font-semibold">
              {patient.bloodGroup}
            </span>
          </div>
        )}

        {/* Active conditions */}
        {conditions.length > 0 && (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Active Conditions</p>
            <div className="flex flex-wrap gap-1">
              {conditions.map((c) => (
                <span key={c} className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px]">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Current medications */}
        {medications.length > 0 && (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Current Medications</p>
            <ul className="space-y-0.5 text-gray-700">
              {medications.map((m) => (
                <li key={m} className="flex items-start gap-1">
                  <span className="text-blue-500 mt-px">•</span>
                  <span className="break-words">{m}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {patient.allergies?.length > 0 && (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Allergies</p>
            <div className="flex flex-wrap gap-1">
              {patient.allergies.map((a) => (
                <span key={a} className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px]">
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {patient.emergencyContact && (
          <div>
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Emergency</p>
            <p className="text-gray-700 break-words">{patient.emergencyContact}</p>
          </div>
        )}

        {/* Latest check-in summary */}
        {latestCheckIn && (
          <div className="border-t border-gray-100 pt-3">
            <p className="text-gray-400 uppercase tracking-wide font-medium mb-1">Last Check-in</p>
            <div className="space-y-0.5 text-gray-600">
              <p>Mood: {latestCheckIn.mood}/10</p>
              <p>Energy: {latestCheckIn.energy}/10</p>
              <p>Sleep: {latestCheckIn.sleep}h</p>
              {latestCheckIn.symptoms?.length > 0 && (
                <p className="text-amber-700">⚠ {latestCheckIn.symptoms.slice(0, 2).join(', ')}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
