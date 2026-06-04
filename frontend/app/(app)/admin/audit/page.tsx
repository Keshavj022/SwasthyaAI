'use client'

import { Info } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import PageHeader from '@/components/ui/PageHeader'
import AuditLogTable from '@/components/admin/AuditLogTable'

export default function AdminAuditPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-7xl mx-auto space-y-4">
          <PageHeader
            title="Audit Logs"
            subtitle="Complete record of AI actions, decisions, and reasoning"
            breadcrumb={[
              { label: 'Admin', href: '/dashboard/admin' },
              { label: 'Audit Logs' },
            ]}
          />

          <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
            <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <p className="text-sm text-blue-800">
              Every AI interaction is logged with its confidence and reasoning. Rows highlighted in
              red triggered an emergency escalation; amber rows had low confidence (&lt;40%). This
              trail supports compliance and clinical oversight — it is not a clinical record.
            </p>
          </div>

          <AuditLogTable />
        </div>
      </div>
    </ProtectedRoute>
  )
}
