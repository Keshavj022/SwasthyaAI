'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useRescheduleAppointment, useDoctorAvailability } from '@/hooks/useAppointments'
import { DateTimeSlotPicker } from './DateTimeSlotPicker'
import type { Appointment } from '@/types'

interface RescheduleDialogProps {
  appointment: Appointment
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function RescheduleDialog({ appointment, open, onOpenChange }: RescheduleDialogProps) {
  const [newSlot, setNewSlot] = useState<string | null>(null)
  const rescheduleMutation = useRescheduleAppointment()

  // Fetch all availability to find this doctor's slots
  const { data: allDoctors, isLoading } = useDoctorAvailability()
  const doctorAvail = allDoctors?.find(
    (d) => d.doctorId === appointment.doctorId || d.doctorName === appointment.doctorName
  )
  const slots = doctorAvail?.slots ?? []

  function handleConfirm() {
    if (!newSlot) return
    rescheduleMutation.mutate(
      {
        appointmentId: appointment.id,
        newDateTime: newSlot,
        patientId: appointment.patientId,
      },
      {
        onSuccess: () => {
          toast.success('Appointment rescheduled')
          onOpenChange(false)
        },
        onError: () => toast.error('Failed to reschedule. Please try another time.'),
      }
    )
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                                    w-full max-w-md bg-white rounded-2xl shadow-xl p-6 focus:outline-none
                                    max-h-[90vh] overflow-y-auto">
          <div className="flex items-start justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Reschedule Appointment
            </Dialog.Title>
            <Dialog.Close className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </Dialog.Close>
          </div>

          <p className="text-sm text-gray-600 mb-1">
            Doctor: <span className="font-medium">{appointment.doctorName ?? appointment.doctorId}</span>
          </p>
          <p className="text-xs text-gray-400 mb-4">Select a new date and time:</p>

          {isLoading ? (
            <div className="h-48 bg-gray-50 rounded-xl animate-pulse" />
          ) : slots.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              No available slots found for this doctor.
            </p>
          ) : (
            <DateTimeSlotPicker
              slots={slots}
              selected={newSlot}
              onChange={setNewSlot}
            />
          )}

          <div className="flex gap-3 mt-6">
            <Dialog.Close asChild>
              <button className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium
                                  text-gray-700 hover:bg-gray-50 transition-colors">
                Cancel
              </button>
            </Dialog.Close>
            <button
              onClick={handleConfirm}
              disabled={!newSlot || rescheduleMutation.isPending}
              className="flex-1 px-4 py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium
                          hover:bg-teal-700 disabled:opacity-40 transition-colors"
            >
              {rescheduleMutation.isPending ? 'Saving...' : 'Confirm'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
