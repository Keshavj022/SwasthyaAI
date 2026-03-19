'use client'

import { useRouter } from 'next/navigation'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { User, Pill, AlertTriangle, ExternalLink, MessageCircle } from 'lucide-react'
import type { Appointment } from '@/types'

interface Props {
  appointment: Appointment | null
  open: boolean
  onClose: () => void
}

export default function PatientSheet({ appointment, open, onClose }: Props) {
  const router = useRouter()

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        {appointment && (() => {
          const patientId = appointment.patientId
          const appointmentTime = new Date(appointment.dateTime).toLocaleString('en-IN', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          })
          return (
            <>
              <SheetHeader className="mb-6">
                <SheetTitle className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-bold">
                    {patientId.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-base font-semibold text-gray-900">{patientId}</p>
                    <p className="text-xs text-gray-500 font-normal">{appointmentTime}</p>
                  </div>
                </SheetTitle>
              </SheetHeader>

              <div className="space-y-5">
                <section>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Appointment
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-full bg-teal-50 text-teal-700 text-xs font-medium capitalize">
                      {appointment.type}
                    </span>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                        appointment.status === 'confirmed'
                          ? 'bg-green-50 text-green-700'
                          : appointment.status === 'scheduled'
                          ? 'bg-blue-50 text-blue-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {appointment.status}
                    </span>
                  </div>
                  {appointment.notes && (
                    <p className="mt-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-2.5">
                      {appointment.notes}
                    </p>
                  )}
                </section>

                <section>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Patient Info
                  </h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-400" />
                      <span>
                        Patient ID:{' '}
                        <span className="font-medium text-gray-900">{patientId}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Pill className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 italic">
                        Medication data loads on full record
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 italic">
                        Allergy data loads on full record
                      </span>
                    </div>
                  </div>
                </section>

                <section className="space-y-2 pt-2 border-t border-gray-100">
                  <button
                    onClick={() => { onClose(); router.push('/records') }}
                    className="flex items-center justify-between w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <ExternalLink className="w-4 h-4" /> Open full record
                    </span>
                  </button>
                  <button
                    onClick={() => {
                      onClose()
                      router.push(`/chat?patientId=${patientId}`)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" /> Start AI consultation
                  </button>
                </section>
              </div>
            </>
          )
        })()}
      </SheetContent>
    </Sheet>
  )
}
