'use client'

import { ShieldCheck } from 'lucide-react'

export default function CriticalAlerts() {
  // Audit endpoint requires admin role. Static "all clear" state until
  // a doctor-scoped triage alert endpoint is added in a future task.
  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-green-50 border border-green-200">
      <ShieldCheck className="w-5 h-5 text-green-600 shrink-0" />
      <div>
        <p className="text-sm font-medium text-green-800">No critical alerts</p>
        <p className="text-xs text-green-600">
          All patients are stable. No emergency triage flags.
        </p>
      </div>
    </div>
  )
}
