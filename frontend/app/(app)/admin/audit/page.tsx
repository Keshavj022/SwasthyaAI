'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { AuditLogTable } from '@/components/admin/AuditLogTable'

function AuditPageInner() {
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-sm text-gray-500 mt-1">All AI agent decisions with confidence scores and escalation flags.</p>
      </div>
      <AuditLogTable />
    </div>
  )
}

export default function AdminAuditPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AuditPageInner />
    </ProtectedRoute>
  )
}
