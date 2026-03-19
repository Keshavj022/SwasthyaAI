'use client'

import type { Appointment } from '@/types'

const STATUS_CONFIG: Record<
  Appointment['status'],
  { label: string; className: string }
> = {
  scheduled: { label: 'Scheduled', className: 'bg-blue-100 text-blue-800' },
  confirmed:  { label: 'Confirmed', className: 'bg-green-100 text-green-800' },
  pending:    { label: 'Pending',   className: 'bg-amber-100 text-amber-800' },
  completed:  { label: 'Completed', className: 'bg-gray-100 text-gray-600' },
  cancelled:  { label: 'Cancelled', className: 'bg-red-100 text-red-700' },
}

interface AppointmentStatusBadgeProps {
  status: Appointment['status']
}

export function AppointmentStatusBadge({ status }: AppointmentStatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? { label: status, className: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
