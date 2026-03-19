'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { toast } from 'sonner'
import { useCancelAppointment } from '@/hooks/useAppointments'
import type { Appointment } from '@/types'
import { AppointmentStatusBadge } from './AppointmentStatusBadge'

interface CancelDialogProps {
  appointment: Appointment
  open: boolean
  onOpenChange: (open: boolean) => void
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

export function CancelDialog({ appointment, open, onOpenChange }: CancelDialogProps) {
  const cancelMutation = useCancelAppointment()

  function handleConfirm() {
    cancelMutation.mutate(
      { appointmentId: appointment.id, patientId: appointment.patientId },
      {
        onSuccess: () => {
          toast.success('Appointment cancelled')
          onOpenChange(false)
        },
        onError: () => toast.error('Failed to cancel appointment'),
      }
    )
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                                    w-full max-w-md bg-white rounded-2xl shadow-xl p-6 focus:outline-none">
          <div className="flex items-start justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Cancel Appointment
            </Dialog.Title>
            <Dialog.Close className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </Dialog.Close>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            Are you sure you want to cancel this appointment?
          </p>

          <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-1.5 text-sm">
            {appointment.doctorName && (
              <p className="font-medium text-gray-900">{appointment.doctorName}</p>
            )}
            <p className="text-gray-600">{formatDateTime(appointment.dateTime)}</p>
            <p className="text-gray-600">Type: {appointment.type}</p>
            <AppointmentStatusBadge status={appointment.status} />
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-6">
            <p className="text-xs text-amber-800">
              Cancellations made 24+ hours in advance receive a full refund.
            </p>
          </div>

          <div className="flex gap-3">
            <Dialog.Close asChild>
              <button className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium
                                  text-gray-700 hover:bg-gray-50 transition-colors">
                Keep Appointment
              </button>
            </Dialog.Close>
            <button
              onClick={handleConfirm}
              disabled={cancelMutation.isPending}
              className="flex-1 px-4 py-2.5 rounded-xl bg-red-600 text-white text-sm font-medium
                          hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {cancelMutation.isPending ? 'Cancelling...' : 'Yes, Cancel'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
