'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Pill, ChevronRight, Check, Clock } from 'lucide-react'

interface MedReminder {
  id: string
  name: string
  dose: string
  time: string
  taken: boolean
}

// Sample data — real medication data is wired in Task 12 (AI prescription integration)
const INITIAL_MEDS: MedReminder[] = [
  { id: '1', name: 'Metformin', dose: '500mg', time: '8:00 AM', taken: true },
  { id: '2', name: 'Lisinopril', dose: '10mg', time: '8:00 AM', taken: true },
  { id: '3', name: 'Aspirin', dose: '75mg', time: '9:00 PM', taken: false },
]

export default function MedicationReminders() {
  const [meds, setMeds] = useState<MedReminder[]>(INITIAL_MEDS)

  const toggle = (id: string) =>
    setMeds((prev) =>
      prev.map((m) => (m.id === id ? { ...m, taken: !m.taken } : m))
    )

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

      <div className="space-y-2">
        {meds.map((med) => (
          <div
            key={med.id}
            className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              med.taken ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'
            }`}>
              <Pill className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900">
                {med.name} <span className="text-gray-500 font-normal">{med.dose}</span>
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
                <><Check className="w-3 h-3" /> Taken</>
              ) : (
                <><Clock className="w-3 h-3" /> Mark taken</>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
