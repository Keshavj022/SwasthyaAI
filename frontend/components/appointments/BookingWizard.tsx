'use client'

import { useState } from 'react'
import { ChevronLeft, Star, Loader2, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { useQueryClient } from '@tanstack/react-query'
import {
  useBook,
  useAvailability,
  appointmentKeys,
  SlotConflictError,
} from '@/hooks/useAppointments'
import { DateTimeSlotPicker } from './DateTimeSlotPicker'
import type { DoctorAvailability } from '@/lib/api'

interface BookingWizardProps {
  patientId: string
  onSuccess: () => void
  /** Pre-fill for "reschedule mode" — start at the date/time step with a doctor. */
  initialDoctor?: DoctorAvailability
  initialStep?: number
}

// ---------------------------------------------------------------------------
// Step 1 config — appointment reasons → suggested specialty + appointment type
// ---------------------------------------------------------------------------

interface ReasonConfig {
  id: string
  label: string
  /** Human appointment type sent to the backend. */
  type: string
  icon: string
  specialty: string
}

const REASONS: ReasonConfig[] = [
  { id: 'general',     label: 'General Check-up',        type: 'Check-up',     icon: '🏥', specialty: 'Family Medicine' },
  { id: 'specialist',  label: 'Specialist Consultation', type: 'Consultation', icon: '🩺', specialty: '' },
  { id: 'follow-up',   label: 'Follow-up',               type: 'Follow-up',    icon: '🔄', specialty: '' },
  { id: 'emergency',   label: 'Emergency',               type: 'Emergency',    icon: '🚨', specialty: 'Internal Medicine' },
  { id: 'lab-review',  label: 'Lab Review',              type: 'Lab Review',   icon: '🧪', specialty: 'Internal Medicine' },
  { id: 'vaccination', label: 'Vaccination',             type: 'Vaccination',  icon: '💉', specialty: 'Family Medicine' },
]

// 9 specialties patients can browse.
const SPECIALTIES = [
  'Cardiology', 'Neurology', 'Dermatology', 'Orthopedics', 'Pediatrics',
  'Family Medicine', 'Internal Medicine', 'Gynecology', 'Oncology',
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
          className={`h-2.5 rounded-full transition-all ${
            i < current
              ? 'w-2.5 bg-teal-600'
              : i === current
              ? 'w-6 bg-teal-500'
              : 'w-2.5 bg-gray-200'
          }`}
        />
      ))}
      <span className="ml-2 text-xs text-gray-500">Step {current + 1} of {total}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Step 2 — doctor card
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
  const hasSlots = doc.slots.length > 0
  const nextSlot = hasSlots
    ? new Date(doc.slots[0]).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })
    : 'No openings'
  const initials = doc.doctorName.replace(/^Dr\.?\s*/i, '').split(' ').map((n) => n[0]).join('').slice(0, 2)

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={!hasSlots}
      className={`w-full text-left p-4 rounded-xl border transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
        selected ? 'border-teal-500 bg-teal-50 shadow-sm' : 'border-gray-200 bg-white hover:border-teal-300'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 text-sm font-bold">
          {initials || 'Dr'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm truncate">{doc.doctorName}</p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="truncate">{doc.specialty}</span>
            <span className="flex items-center gap-0.5 text-amber-500">
              <Star size={10} fill="currentColor" /> 4.8
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Next available: <span className={hasSlots ? 'text-teal-700 font-medium' : 'text-gray-400'}>{nextSlot}</span>
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
  const qc = useQueryClient()
  const [step, setStep] = useState(initialDoctor ? 2 : initialStep)
  const [reason, setReason] = useState<ReasonConfig | null>(null)
  const [specialty, setSpecialty] = useState<string>(initialDoctor?.specialty ?? '')
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorAvailability | null>(initialDoctor ?? null)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [conflictNote, setConflictNote] = useState<string | null>(null)

  const { data: doctors, isLoading: loadingDoctors, isError: doctorsError, refetch } =
    useAvailability(specialty || undefined)
  const bookMutation = useBook()

  // Keep the working copy of the selected doctor's slots fresh: after a conflict
  // we refetch availability, so re-resolve the selected doctor's latest slots.
  const liveDoctor =
    selectedDoctor && doctors
      ? doctors.find((d) => d.doctorId === selectedDoctor.doctorId) ?? selectedDoctor
      : selectedDoctor

  const apptType = reason?.type ?? 'Consultation'

  // ---- Step 1: reason ------------------------------------------------------
  if (step === 0) {
    return (
      <div>
        <StepIndicator current={0} total={4} />
        <h2 className="text-base font-semibold text-gray-900 mb-4">What&apos;s the reason for your visit?</h2>
        <div className="grid grid-cols-2 gap-3">
          {REASONS.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => {
                setReason(r)
                setSpecialty(r.specialty)
                setSelectedDoctor(null)
                setSelectedSlot(null)
                setStep(1)
              }}
              className="flex flex-col items-center gap-2 p-5 rounded-xl border border-gray-200 bg-white
                          hover:border-teal-400 hover:bg-teal-50 transition-all text-center"
            >
              <span className="text-3xl" aria-hidden>{r.icon}</span>
              <span className="text-xs font-medium text-gray-700">{r.label}</span>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // ---- Step 2: specialty + doctor -----------------------------------------
  if (step === 1) {
    return (
      <div>
        <StepIndicator current={1} total={4} />
        <button
          type="button"
          onClick={() => setStep(0)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4"
        >
          <ChevronLeft size={14} /> Back
        </button>
        <h2 className="text-base font-semibold text-gray-900 mb-3">Choose specialty &amp; doctor</h2>

        <div className="mb-4">
          <label className="text-xs font-medium text-gray-600 mb-1 block">Specialty</label>
          <select
            value={specialty}
            onChange={(e) => { setSpecialty(e.target.value); setSelectedDoctor(null); setSelectedSlot(null) }}
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All specialties</option>
            {SPECIALTIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {loadingDoctors ? (
          <div className="space-y-3">
            {[1, 2].map((i) => <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />)}
          </div>
        ) : doctorsError ? (
          <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center">
            <p className="text-sm text-red-600 mb-2">Couldn&apos;t load doctors.</p>
            <button onClick={() => refetch()} className="text-xs text-teal-600 hover:underline">
              Try again
            </button>
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
                onSelect={() => { setSelectedDoctor(doc); setSelectedSlot(null) }}
              />
            ))}
          </div>
        )}

        <button
          type="button"
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

  // ---- Step 3: date & time -------------------------------------------------
  if (step === 2) {
    const slots = liveDoctor?.slots ?? []
    return (
      <div>
        <StepIndicator current={2} total={4} />
        <button
          type="button"
          onClick={() => setStep(initialDoctor ? 2 : 1)}
          disabled={!!initialDoctor}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4 disabled:opacity-0"
        >
          <ChevronLeft size={14} /> Back
        </button>
        <h2 className="text-base font-semibold text-gray-900 mb-1">Choose date &amp; time</h2>
        {liveDoctor && (
          <p className="text-xs text-gray-500 mb-4">with {liveDoctor.doctorName}</p>
        )}

        {conflictNote && (
          <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 mb-4">
            <AlertTriangle size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-amber-800">{conflictNote}</p>
          </div>
        )}

        {slots.length === 0 ? (
          <div className="text-center py-8 text-sm text-gray-400">
            No open slots for this doctor in the next two weeks.
          </div>
        ) : (
          <DateTimeSlotPicker
            slots={slots}
            selected={selectedSlot}
            onChange={(iso) => { setSelectedSlot(iso); setConflictNote(null) }}
          />
        )}

        <button
          type="button"
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

  // ---- Step 4: confirm -----------------------------------------------------
  async function handleConfirm() {
    if (!selectedDoctor || !selectedSlot) return
    bookMutation.mutate(
      {
        patientId,
        doctorId: selectedDoctor.doctorId,
        dateTime: selectedSlot,
        type: apptType,
        notes: notes || undefined,
      },
      {
        onSuccess: () => {
          toast.success('Appointment booked successfully')
          onSuccess()
        },
        onError: async (err) => {
          if (err instanceof SlotConflictError) {
            // Refresh availability so the picker reflects the now-taken slot,
            // then send the patient back to step 3 to pick again.
            await qc.invalidateQueries({ queryKey: appointmentKeys.availability(specialty || undefined) })
            await refetch()
            setSelectedSlot(null)
            setConflictNote(
              err.nextAvailableSlots.length
                ? 'That slot was just taken. Other times are available below — please pick one.'
                : 'Slot no longer available — please choose another time.'
            )
            toast.error('Slot no longer available — please choose another time')
            setStep(2)
          } else {
            toast.error(err.message || 'Failed to book appointment. Please try again.')
          }
        },
      }
    )
  }

  return (
    <div>
      <StepIndicator current={3} total={4} />
      <button
        type="button"
        onClick={() => setStep(2)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-4"
      >
        <ChevronLeft size={14} /> Back
      </button>
      <h2 className="text-base font-semibold text-gray-900 mb-4">Confirm your appointment</h2>

      <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm mb-4">
        <div className="flex justify-between">
          <span className="text-gray-500">Doctor</span>
          <span className="font-medium text-gray-900">{selectedDoctor?.doctorName}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Specialty</span>
          <span className="text-gray-900">{selectedDoctor?.specialty}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Date &amp; Time</span>
          <span className="text-gray-900">{selectedSlot ? new Date(selectedSlot).toLocaleString('en-IN', {
            weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
          }) : '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Type</span>
          <span className="text-gray-900">{apptType}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Duration</span>
          <span className="text-gray-900">30 min</span>
        </div>
      </div>

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
        type="button"
        onClick={handleConfirm}
        disabled={bookMutation.isPending}
        className="w-full py-2.5 rounded-xl bg-teal-600 text-white text-sm font-semibold
                    hover:bg-teal-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
      >
        {bookMutation.isPending && <Loader2 size={15} className="animate-spin" />}
        {bookMutation.isPending ? 'Booking...' : 'Confirm Booking'}
      </button>
    </div>
  )
}
