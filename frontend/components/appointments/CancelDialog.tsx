'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { useCancel } from '@/hooks/useAppointments'
import type { Appointment } from '@/types'
import { AppointmentStatusBadge } from './AppointmentStatusBadge'

interface CancelDialogProps {
  appointment: Appointment
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Called after a successful cancellation (e.g. to close a popover). */
  onCancelled?: () => void
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

/** Whether the appointment is 24+ hours away (eligible for a full refund). */
function isRefundEligible(iso: string): boolean {
  const diffMs = new Date(iso).getTime() - Date.now()
  return diffMs >= 24 * 60 * 60 * 1000
}

export function CancelDialog({ appointment, open, onOpenChange, onCancelled }: CancelDialogProps) {
  const cancelMutation = useCancel()
  const refundEligible = isRefundEligible(appointment.dateTime)

  function handleConfirm() {
    cancelMutation.mutate(
      {
        appointmentId: appointment.id,
        patientId: appointment.patientId,
        doctorId: appointment.doctorId,
      },
      {
        onSuccess: () => {
          toast.success('Appointment cancelled')
          onCancelled?.()
          onOpenChange(false)
        },
        onError: (err) => toast.error(err.message || 'Failed to cancel appointment'),
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
            {appointment.specialty && (
              <p className="text-xs text-gray-500">{appointment.specialty}</p>
            )}
            <p className="text-gray-600">{formatDateTime(appointment.dateTime)}</p>
            <p className="text-gray-600">Type: {appointment.type}</p>
            <AppointmentStatusBadge status={appointment.status} />
          </div>

          <div
            className={`flex items-start gap-2 rounded-lg px-3 py-2 mb-6 border ${
              refundEligible
                ? 'bg-emerald-50 border-emerald-200'
                : 'bg-amber-50 border-amber-200'
            }`}
          >
            <AlertTriangle
              size={14}
              className={`mt-0.5 flex-shrink-0 ${refundEligible ? 'text-emerald-600' : 'text-amber-600'}`}
            />
            <p className={`text-xs ${refundEligible ? 'text-emerald-800' : 'text-amber-800'}`}>
              {refundEligible
                ? 'This appointment is 24+ hours away — you are eligible for a full refund.'
                : 'Cancellations made 24+ hours in advance receive a full refund. This appointment is within 24 hours, so a refund may not apply.'}
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
              type="button"
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
