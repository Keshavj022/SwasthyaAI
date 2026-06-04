'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import PageHeader from '@/components/ui/PageHeader'
import SystemHealthDashboard from '@/components/admin/SystemHealthDashboard'

export default function AdminSystemPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-7xl mx-auto">
          <PageHeader
            title="System Health"
            subtitle="Live infrastructure and AI model status"
            breadcrumb={[
              { label: 'Admin', href: '/dashboard/admin' },
              { label: 'System Health' },
            ]}
          />
          <SystemHealthDashboard />
        </div>
      </div>
    </ProtectedRoute>
  )
}
