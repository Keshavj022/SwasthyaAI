'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Pill, ChevronRight, Check, Clock, Info } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { usePatient } from '@/hooks/usePatients'

interface MedReminder {
  id: string
  name: string
  dose: string
  time: string
  taken: boolean
}

// Fallback sample data — clearly labelled as a sample. Real adherence/schedule
// data arrives in Task 12 (AI prescription integration).
const SAMPLE_MEDS: MedReminder[] = [
  { id: 's1', name: 'Metformin', dose: '500mg', time: '8:00 AM', taken: true },
  { id: 's2', name: 'Lisinopril', dose: '10mg', time: '8:00 AM', taken: true },
  { id: 's3', name: 'Aspirin', dose: '75mg', time: '9:00 PM', taken: false },
]

const DEFAULT_TIMES = ['8:00 AM', '1:00 PM', '9:00 PM']

/**
 * Parse a free-text medication string from the patient record into a
 * name + dose pair. e.g. "Metformin 500mg", "Lisinopril 10 mg".
 */
function parseMedication(raw: string, index: number): MedReminder {
  const trimmed = raw.trim()
  const match = trimmed.match(/^(.*?)(\s+\d+\.?\d*\s*(?:mg|mcg|g|ml|units?|iu)\b.*)$/i)
  return {
    id: `m${index}`,
    name: match ? match[1].trim() : trimmed,
    dose: match ? match[2].trim() : '',
    time: DEFAULT_TIMES[index % DEFAULT_TIMES.length],
    taken: false,
  }
}

interface Props {
  patientId?: string
}

export default function MedicationReminders({ patientId }: Props) {
  const { data: patient, isLoading } = usePatient(patientId ?? '')

  const realMeds = useMemo<MedReminder[] | null>(() => {
    const list = patient?.currentMedications
    if (list && list.length > 0) {
      return list.map((m, i) => parseMedication(m, i))
    }
    return null
  }, [patient])

  const usingSample = realMeds === null
  const [meds, setMeds] = useState<MedReminder[]>(SAMPLE_MEDS)

  useEffect(() => {
    setMeds(realMeds ?? SAMPLE_MEDS)
  }, [realMeds])

  const toggle = (id: string) =>
    setMeds((prev) => prev.map((m) => (m.id === id ? { ...m, taken: !m.taken } : m)))

  if (patientId && isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
        <Skeleton className="h-5 w-40" />
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Medications Today</h2>
        <Link
          href="/medications"
          className="text-xs text-teal-600 font-medium hover:underline flex items-center gap-0.5"
        >
          View all <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {usingSample && (
        <div className="flex items-start gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 border border-amber-100">
          <Info className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
          <p className="text-xs text-amber-700">
            Sample schedule — add your medications to your profile to see real reminders.
          </p>
        </div>
      )}

      <div className="space-y-2">
        {meds.map((med) => (
          <div
            key={med.id}
            className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                med.taken ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'
              }`}
            >
              <Pill className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {med.name}
                {med.dose && <span className="text-gray-500 font-normal"> {med.dose}</span>}
              </p>
              <p className="text-xs text-gray-500">{med.time}</p>
            </div>
            <button
              onClick={() => toggle(med.id)}
              className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full transition-colors ${
                med.taken
                  ? 'bg-green-50 text-green-700 hover:bg-green-100'
                  : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
              }`}
            >
              {med.taken ? (
                <>
                  <Check className="w-3 h-3" /> Taken
                </>
              ) : (
                <>
                  <Clock className="w-3 h-3" /> Mark taken
                </>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
