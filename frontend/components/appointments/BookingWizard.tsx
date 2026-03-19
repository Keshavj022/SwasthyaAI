'use client'

import { useState } from 'react'
import { ChevronLeft, Star } from 'lucide-react'
import { toast } from 'sonner'
import { useBookAppointment, useDoctorAvailability } from '@/hooks/useAppointments'
import { DateTimeSlotPicker } from './DateTimeSlotPicker'
import type { DoctorAvailability } from '@/lib/api'

interface BookingWizardProps {
  patientId: string
  onSuccess: () => void
  // Pre-fill for "reschedule mode" — skip to step 2 with pre-selected doctor
  initialDoctor?: DoctorAvailability
  initialStep?: number
}

// ---------------------------------------------------------------------------
// Step 1 config — appointment reasons
// ---------------------------------------------------------------------------

const REASONS = [
  { id: 'general',      label: 'General Check-up',         icon: '🏥', specialty: 'General Medicine' },
  { id: 'specialist',   label: 'Specialist Consultation',  icon: '👨‍⚕️', specialty: '' },
  { id: 'follow-up',    label: 'Follow-up',                icon: '🔄', specialty: 'General Medicine' },
  { id: 'emergency',    label: 'Emergency',                icon: '🚨', specialty: 'Emergency Medicine' },
  { id: 'lab-review',   label: 'Lab Review',               icon: '🧪', specialty: 'Pathology' },
  { id: 'vaccination',  label: 'Vaccination',              icon: '💉', specialty: 'General Medicine' },
]

const SPECIALTIES = [
  'General Medicine', 'Cardiology', 'Neurology', 'Dermatology',
  'Orthopedics', 'Pediatrics', 'Gynecology', 'Oncology', 'Emergency Medicine',
]

// ---------------------------------------------------------------------------
// Step indicator
// ---------------------------------------------------------------------------

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`w-2.5 h-2.5 rounded-full transition-colors ${
            i < current ? 'bg-teal-600' : i === current ? 'bg-teal-400' : 'bg-gray-200'
          }`}
        />
      ))}
      <span className="ml-2 text-xs text-gray-500">Step {current + 1} of {total}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Step 2 — doctor selection
// ---------------------------------------------------------------------------

function DoctorCard({
  doc,
  selected,
  onSelect,
}: {
  doc: DoctorAvailability
  selected: boolean
  onSelect: () => void
}) {
  const nextSlot = doc.slots[0]
    ? new Date(doc.slots[0]).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })
    : 'No slots'

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border transition-all ${
        selected ? 'border-teal-500 bg-teal-50 shadow-sm' : 'border-gray-200 bg-white hover:border-teal-300'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Avatar placeholder */}
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 text-sm font-bold">
          {doc.doctorName.split(' ').map((n) => n[0]).join('').slice(0, 2)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm">{doc.doctorName}</p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{doc.specialty}</span>
            <span className="flex items-center gap-0.5 text-amber-500">
              <Star size={10} fill="currentColor" /> 4.8
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Next available: <span className="text-teal-700 font-medium">{nextSlot}</span>
          </p>
        </div>
        {selected && (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-teal-600 flex items-center justify-center">
            <span className="text-white text-xs">✓</span>
          </div>
        )}
      </div>
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main wizard
// ---------------------------------------------------------------------------

export function BookingWizard({
  patientId,
  onSuccess,
  initialDoctor,
  initialStep = 0,
}: BookingWizardProps) {
  const [step, setStep] = useState(initialDoctor ? 2 : initialStep)
  const [reason, setReason] = useState<string>('')
  const [specialty, setSpecialty] = useState<string>('')
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorAvailability | null>(initialDoctor ?? null)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [notes, setNotes] = useState('')

  const { data: doctors, isLoading: loadingDoctors } = useDoctorAvailability(specialty || undefined)
  const bookMutation = useBookAppointment()

  // Step 1: select reason
  if (step === 0) {
    return (
      <div>
        <StepIndicator current={0} total={4} />
        <h2 className="text-base font-semibold text-gray-900 mb-4">What's the reason for your visit?</h2>
        <div className="grid grid-cols-2 gap-3">
          {REASONS.map((r) => (
            <button
              key={r.id}
              onClick={() => {
                setReason(r.id)
                if (r.specialty) setSpecialty(r.specialty)
                setStep(1)
              }}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 bg-white
                          hover:border-teal-400 hover:bg-teal-50 transition-all text-center"
            >
              <span className="text-2xl">{r.icon}</span>
              <span className="text-xs font-medium text-gray-700">{r.label}</span>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Step 2: choose specialty + doctor
  if (step === 1) {
    return (
      <div>
        <StepIndicator current={1} total={4} />
        <button onClick={() => setStep(0)} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4">
          <ChevronLeft size={14} /> Back
        </button>
        <h2 className="text-base font-semibold text-gray-900 mb-3">Choose specialty & doctor</h2>

        {/* Specialty selector */}
        <div className="mb-4">
          <label className="text-xs font-medium text-gray-600 mb-1 block">Specialty</label>
          <select
            value={specialty}
            onChange={(e) => { setSpecialty(e.target.value); setSelectedDoctor(null) }}
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All specialties</option>
            {SPECIALTIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Doctor cards */}
        {loadingDoctors ? (
          <div className="space-y-3">
            {[1, 2].map((i) => <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />)}
          </div>
        ) : !doctors?.length ? (
          <div className="text-center py-8 text-sm text-gray-400">
            No doctors available for this specialty.
          </div>
        ) : (
          <div className="space-y-3">
            {doctors.map((doc) => (
              <DoctorCard
                key={doc.doctorId}
                doc={doc}
                selected={selectedDoctor?.doctorId === doc.doctorId}
                onSelect={() => setSelectedDoctor(doc)}
              />
            ))}
          </div>
        )}

        <button
          onClick={() => setStep(2)}
          disabled={!selectedDoctor}
          className="mt-4 w-full py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium
                      hover:bg-teal-700 disabled:opacity-40 transition-colors"
        >
          Continue
        </button>
      </div>
    )
  }

  // Step 3: date and time
  if (step === 2) {
    return (
      <div>
        <StepIndicator current={2} total={4} />
        <button onClick={() => setStep(1)} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4">
          <ChevronLeft size={14} /> Back
        </button>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Choose date & time</h2>

        {selectedDoctor && (
          <DateTimeSlotPicker
            slots={selectedDoctor.slots}
            selected={selectedSlot}
            onChange={setSelectedSlot}
          />
        )}

        <button
          onClick={() => setStep(3)}
          disabled={!selectedSlot}
          className="mt-4 w-full py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium
                      hover:bg-teal-700 disabled:opacity-40 transition-colors"
        >
          Continue
        </button>
      </div>
    )
  }

  // Step 4: confirm
  function handleConfirm() {
    if (!selectedDoctor || !selectedSlot) return

    bookMutation.mutate(
      {
        patientId,
        doctorId: selectedDoctor.doctorId,
        dateTime: selectedSlot,
        type: reason || 'consultation',
        notes: notes || undefined,
      },
      {
        onSuccess: () => {
          toast.success('Appointment booked successfully!')
          onSuccess()
        },
        onError: (err) => {
          // Heuristic: slot conflict usually mentioned in error message
          const msg = err.message?.toLowerCase() ?? ''
          if (msg.includes('conflict') || msg.includes('unavailable') || msg.includes('slot')) {
            toast.error('Slot no longer available — please choose another time')
            setStep(2)
          } else {
            toast.error('Failed to book appointment. Please try again.')
          }
        },
      }
    )
  }

  return (
    <div>
      <StepIndicator current={3} total={4} />
      <button onClick={() => setStep(2)} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4">
        <ChevronLeft size={14} /> Back
      </button>
      <h2 className="text-base font-semibold text-gray-900 mb-4">Confirm your appointment</h2>

      {/* Summary card */}
      <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm mb-4">
        <div className="flex justify-between">
          <span className="text-gray-500">Doctor</span>
          <span className="font-medium">{selectedDoctor?.doctorName}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Specialty</span>
          <span>{selectedDoctor?.specialty}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Date & Time</span>
          <span>{selectedSlot ? new Date(selectedSlot).toLocaleString('en-IN', {
            weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
          }) : '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Type</span>
          <span className="capitalize">{reason || 'consultation'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Duration</span>
          <span>30 min</span>
        </div>
      </div>

      {/* Notes */}
      <div className="mb-4">
        <label className="text-xs font-medium text-gray-600 mb-1 block">
          Notes (optional, max 200 chars)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value.slice(0, 200))}
          rows={3}
          placeholder="Any symptoms or information for the doctor..."
          className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm resize-none
                      focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        <p className="text-xs text-gray-400 text-right">{notes.length}/200</p>
      </div>

      <button
        onClick={handleConfirm}
        disabled={bookMutation.isPending}
        className="w-full py-2.5 rounded-xl bg-teal-600 text-white text-sm font-semibold
                    hover:bg-teal-700 disabled:opacity-50 transition-colors"
      >
        {bookMutation.isPending ? 'Booking...' : 'Confirm Booking'}
      </button>
    </div>
  )
}
