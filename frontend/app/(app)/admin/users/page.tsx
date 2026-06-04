'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import PageHeader from '@/components/ui/PageHeader'
import UserTable from '@/components/admin/UserTable'

export default function AdminUsersPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-7xl mx-auto">
          <PageHeader
            title="User Management"
            subtitle="View, search, and manage all system accounts"
            breadcrumb={[
              { label: 'Admin', href: '/dashboard/admin' },
              { label: 'Users' },
            ]}
          />
          <UserTable />
        </div>
      </div>
    </ProtectedRoute>
  )
}
