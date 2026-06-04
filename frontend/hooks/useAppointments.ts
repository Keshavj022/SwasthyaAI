'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { appointmentApi, apiClient } from '@/lib/api'
import type { DoctorAvailability, BookAppointmentPayload } from '@/lib/api'
import type { Appointment } from '@/types'

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const appointmentKeys = {
  all: ['appointments'] as const,
  byPatient: (patientId: string) => ['appointments', 'patient', patientId] as const,
  byDoctor: (doctorId: string) => ['appointments', 'doctor', doctorId] as const,
  availability: (specialty?: string, doctorName?: string) =>
    ['appointments', 'availability', specialty ?? 'all', doctorName ?? 'any'] as const,
}

// ---------------------------------------------------------------------------
// Error helpers — surface the backend conflict envelope (HTTP 409)
// ---------------------------------------------------------------------------

/**
 * The booking / reschedule endpoints return HTTP 409 on a slot conflict with a
 * structured detail: `{ message, next_available_slots }`. This error subclass
 * carries that payload so the UI can offer the next available times.
 */
export class SlotConflictError extends Error {
  nextAvailableSlots: string[]
  constructor(message: string, nextAvailableSlots: string[]) {
    super(message)
    this.name = 'SlotConflictError'
    this.nextAvailableSlots = nextAvailableSlots
  }
}

/** Normalise an axios error into a typed Error, detecting slot conflicts. */
function normalizeError(err: unknown): Error {
  if (err instanceof AxiosError) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 409) {
      // detail may be a string or { message, next_available_slots }
      if (detail && typeof detail === 'object') {
        return new SlotConflictError(
          detail.message ?? 'Slot no longer available — please choose another time',
          Array.isArray(detail.next_available_slots) ? detail.next_available_slots : []
        )
      }
      return new SlotConflictError(
        typeof detail === 'string' ? detail : 'Slot no longer available — please choose another time',
        []
      )
    }
    if (typeof detail === 'string') return new Error(detail)
    if (detail && typeof detail === 'object' && detail.message) return new Error(detail.message)
    return new Error(err.message || 'Request failed')
  }
  return err instanceof Error ? err : new Error('Unknown error')
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** A patient's appointments (backend constrains to the authenticated patient). */
export function useMyAppointments(patientId: string) {
  return useQuery<Appointment[], Error>({
    queryKey: appointmentKeys.byPatient(patientId),
    queryFn: () => appointmentApi.getByPatient(patientId),
    enabled: !!patientId,
  })
}

/** A doctor's full schedule (backend constrains to the authenticated doctor). */
export function useDoctorSchedule(doctorId: string) {
  return useQuery<Appointment[], Error>({
    queryKey: appointmentKeys.byDoctor(doctorId),
    queryFn: async () => {
      const { data } = await apiClient.get<Appointment[]>(
        `/api/appointments?doctor_id=${encodeURIComponent(doctorId)}`
      )
      return data
    },
    enabled: !!doctorId,
  })
}

/** Bookable availability per doctor, optionally filtered by specialty / name. */
export function useAvailability(specialty?: string, doctorName?: string) {
  return useQuery<DoctorAvailability[], Error>({
    queryKey: appointmentKeys.availability(specialty, doctorName),
    queryFn: () => appointmentApi.getAvailability(specialty, doctorName),
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Book a new appointment. Invalidates the booking patient's list on success. */
export function useBook() {
  const qc = useQueryClient()
  return useMutation<Appointment, Error, BookAppointmentPayload>({
    mutationFn: async (payload) => {
      try {
        return await appointmentApi.book(payload)
      } catch (err) {
        throw normalizeError(err)
      }
    },
    onSuccess: (appt) => {
      qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(appt.patientId) })
      qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(appt.doctorId) })
      qc.invalidateQueries({ queryKey: ['appointments', 'availability'] })
    },
  })
}

/** Reschedule an existing appointment to a new datetime. */
export function useReschedule() {
  const qc = useQueryClient()
  return useMutation<
    Appointment,
    Error,
    { appointmentId: string; newDateTime: string; patientId?: string; doctorId?: string }
  >({
    mutationFn: async ({ appointmentId, newDateTime }) => {
      try {
        return await appointmentApi.reschedule(appointmentId, newDateTime)
      } catch (err) {
        throw normalizeError(err)
      }
    },
    onSuccess: (appt, vars) => {
      if (vars.patientId) qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(vars.patientId) })
      if (vars.doctorId) qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(vars.doctorId) })
      qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(appt.patientId) })
      qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(appt.doctorId) })
      qc.invalidateQueries({ queryKey: ['appointments', 'availability'] })
    },
  })
}

/** Cancel an appointment (soft status change to "cancelled"). */
export function useCancel() {
  const qc = useQueryClient()
  return useMutation<
    { success: boolean },
    Error,
    { appointmentId: string; patientId?: string; doctorId?: string }
  >({
    mutationFn: async ({ appointmentId }) => {
      try {
        return await appointmentApi.cancel(appointmentId)
      } catch (err) {
        throw normalizeError(err)
      }
    },
    onSuccess: (_, vars) => {
      if (vars.patientId) qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(vars.patientId) })
      if (vars.doctorId) qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(vars.doctorId) })
      qc.invalidateQueries({ queryKey: ['appointments', 'availability'] })
    },
  })
}

/** Update an appointment's status (e.g. mark complete) without changing time. */
export function useUpdateStatus() {
  const qc = useQueryClient()
  return useMutation<
    Appointment,
    Error,
    { appointmentId: string; status: Appointment['status']; patientId?: string; doctorId?: string }
  >({
    mutationFn: async ({ appointmentId, status }) => {
      try {
        const { data } = await apiClient.patch<Appointment>(
          `/api/appointments/${appointmentId}`,
          { status }
        )
        return data
      } catch (err) {
        throw normalizeError(err)
      }
    },
    onSuccess: (appt, vars) => {
      if (vars.patientId) qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(vars.patientId) })
      if (vars.doctorId) qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(vars.doctorId) })
      qc.invalidateQueries({ queryKey: appointmentKeys.byDoctor(appt.doctorId) })
    },
  })
}

// ---------------------------------------------------------------------------
// Backward-compatible aliases (older imports)
// ---------------------------------------------------------------------------

export const useDoctorAvailability = useAvailability
export const useDoctorAppointments = useDoctorSchedule
export const useBookAppointment = useBook
export const useRescheduleAppointment = useReschedule
export const useCancelAppointment = useCancel
