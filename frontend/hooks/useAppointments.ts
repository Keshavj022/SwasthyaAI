'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appointmentApi, apiClient } from '@/lib/api'
import type { DoctorAvailability, BookAppointmentPayload } from '@/lib/api'
import type { Appointment } from '@/types'

export const appointmentKeys = {
  byPatient: (patientId: string) => ['appointments', 'patient', patientId] as const,
  availability: (specialty?: string) => ['appointments', 'availability', specialty ?? 'all'] as const,
}

export function useMyAppointments(patientId: string) {
  return useQuery<Appointment[], Error>({
    queryKey: appointmentKeys.byPatient(patientId),
    queryFn: () => appointmentApi.getByPatient(patientId),
    enabled: !!patientId,
  })
}

export function useDoctorAvailability(specialty?: string, doctorName?: string) {
  return useQuery<DoctorAvailability[], Error>({
    queryKey: appointmentKeys.availability(specialty),
    queryFn: () => appointmentApi.getAvailability(specialty, doctorName),
  })
}

export function useBookAppointment() {
  const qc = useQueryClient()
  return useMutation<Appointment, Error, BookAppointmentPayload>({
    mutationFn: appointmentApi.book,
    onSuccess: (appt) => {
      qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(appt.patientId) })
    },
  })
}

export function useRescheduleAppointment() {
  const qc = useQueryClient()
  return useMutation<Appointment, Error, { appointmentId: string; newDateTime: string; patientId: string }>({
    mutationFn: ({ appointmentId, newDateTime }) =>
      appointmentApi.reschedule(appointmentId, newDateTime),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(patientId) })
    },
  })
}

export function useCancelAppointment() {
  const qc = useQueryClient()
  return useMutation<{ success: boolean }, Error, { appointmentId: string; patientId: string }>({
    mutationFn: ({ appointmentId }) => appointmentApi.cancel(appointmentId),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: appointmentKeys.byPatient(patientId) })
    },
  })
}

export function useDoctorAppointments(doctorId: string) {
  return useQuery<Appointment[], Error>({
    queryKey: ['appointments', 'doctor', doctorId] as const,
    queryFn: async () => {
      const { data } = await apiClient.get<Appointment[]>(`/api/appointments?doctor_id=${doctorId}`)
      return data
    },
    enabled: !!doctorId,
  })
}
