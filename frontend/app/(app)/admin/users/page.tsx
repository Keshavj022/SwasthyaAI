'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { UserTable } from '@/components/admin/UserTable'

function UsersPageInner() {
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">User Management</h1>
        <p className="text-sm text-gray-500 mt-1">Manage accounts, roles, and access across the system.</p>
      </div>
      <UserTable />
    </div>
  )
}

export default function AdminUsersPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <UsersPageInner />
    </ProtectedRoute>
  )
}
