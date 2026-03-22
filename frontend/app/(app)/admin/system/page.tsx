'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { SystemHealthDashboard } from '@/components/admin/SystemHealthDashboard'

function SystemPageInner() {
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">System Health</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time status — refreshes every 30 seconds.</p>
      </div>
      <SystemHealthDashboard />
    </div>
  )
}

export default function AdminSystemPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <SystemPageInner />
    </ProtectedRoute>
  )
}
