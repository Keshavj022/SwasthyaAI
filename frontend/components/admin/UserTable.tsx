'use client'

import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  Search,
  Trash2,
  ShieldCheck,
  Stethoscope,
  User as UserIcon,
  Power,
  RefreshCw,
  AlertTriangle,
  Users as UsersIcon,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { adminApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { AdminUser } from '@/types'

type RoleFilter = 'all' | 'doctor' | 'patient' | 'admin'
type StatusFilter = 'all' | 'active' | 'inactive'

const ROLE_META: Record<
  AdminUser['role'],
  { label: string; badge: string; icon: typeof UserIcon }
> = {
  admin: { label: 'Admin', badge: 'bg-red-100 text-red-700', icon: ShieldCheck },
  doctor: { label: 'Doctor', badge: 'bg-blue-100 text-blue-700', icon: Stethoscope },
  patient: { label: 'Patient', badge: 'bg-teal-100 text-teal-700', icon: UserIcon },
}

const adminUserKeys = {
  list: ['admin', 'users'] as const,
}

function fmtDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}

export default function UserTable() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [pendingDelete, setPendingDelete] = useState<AdminUser | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<AdminUser[], Error>({
    queryKey: adminUserKeys.list,
    queryFn: () => adminApi.getUsers(),
  })

  const updateMutation = useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: string
      payload: Partial<{ role: string; isActive: boolean }>
    }) => adminApi.updateUser(userId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminUserKeys.list })
      toast.success('User updated')
    },
    onError: (e: Error) => toast.error(e.message || 'Failed to update user'),
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminUserKeys.list })
      toast.success('User deleted')
      setPendingDelete(null)
    },
    onError: (e: Error) => {
      toast.error(e.message || 'Failed to delete user')
      setPendingDelete(null)
    },
  })

  const users = data ?? []

  const filtered = useMemo(() => {
    return users.filter((u) => {
      if (roleFilter !== 'all' && u.role !== roleFilter) return false
      if (statusFilter === 'active' && !u.isActive) return false
      if (statusFilter === 'inactive' && u.isActive) return false
      if (search.trim()) {
        const q = search.trim().toLowerCase()
        if (!`${u.name} ${u.email}`.toLowerCase().includes(q)) return false
      }
      return true
    })
  }, [users, roleFilter, statusFilter, search])

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="lg:col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name or email..."
                className="w-full h-9 rounded-md border border-gray-200 pl-8 pr-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Role</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as RoleFilter)}
              className="w-full h-9 rounded-md border border-gray-200 px-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
            >
              <option value="all">All roles</option>
              <option value="doctor">Doctors</option>
              <option value="patient">Patients</option>
              <option value="admin">Admins</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="w-full h-9 rounded-md border border-gray-200 px-2.5 text-sm text-gray-900 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-gray-500">
            {isLoading ? 'Loading…' : `${filtered.length} of ${users.length} users`}
          </p>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', isFetching && 'animate-spin')} /> Refresh
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-6">
            <div className="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 p-4">
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-800">Failed to load users</p>
                <p className="mt-1 text-sm text-red-700">
                  {error?.message || 'The admin users endpoint did not respond.'}
                </p>
                <button
                  onClick={() => refetch()}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Retry
                </button>
              </div>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<UsersIcon className="w-6 h-6" />}
            title="No users found"
            description="No users match the current filters."
            className="py-12"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr className="text-left text-xs font-semibold text-gray-500">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((u) => {
                  const meta = ROLE_META[u.role]
                  const RoleIcon = meta.icon
                  const busy =
                    (updateMutation.isPending && updateMutation.variables?.userId === u.id) ||
                    (deleteMutation.isPending && deleteMutation.variables === u.id)
                  return (
                    <tr key={u.id} className={cn('hover:bg-gray-50 transition-colors', busy && 'opacity-60')}>
                      <td className="px-4 py-3 font-medium text-gray-900">{u.name}</td>
                      <td className="px-4 py-3 text-gray-600">{u.email}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                              meta.badge
                            )}
                          >
                            <RoleIcon className="w-3 h-3" />
                            {meta.label}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium',
                            u.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                          )}
                        >
                          <span
                            className={cn(
                              'w-1.5 h-1.5 rounded-full',
                              u.isActive ? 'bg-green-500' : 'bg-gray-400'
                            )}
                          />
                          {u.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                        {fmtDate(u.createdAt)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <select
                            value={u.role}
                            disabled={busy}
                            onChange={(e) =>
                              updateMutation.mutate({
                                userId: u.id,
                                payload: { role: e.target.value },
                              })
                            }
                            aria-label={`Change role for ${u.name}`}
                            className="h-8 rounded-md border border-gray-200 px-2 text-xs text-gray-700 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none disabled:opacity-50"
                          >
                            <option value="patient">Patient</option>
                            <option value="doctor">Doctor</option>
                            <option value="admin">Admin</option>
                          </select>
                          <button
                            disabled={busy}
                            onClick={() =>
                              updateMutation.mutate({
                                userId: u.id,
                                payload: { isActive: !u.isActive },
                              })
                            }
                            title={u.isActive ? 'Deactivate' : 'Activate'}
                            className={cn(
                              'inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors disabled:opacity-50',
                              u.isActive
                                ? 'border-amber-200 text-amber-700 hover:bg-amber-50'
                                : 'border-green-200 text-green-700 hover:bg-green-50'
                            )}
                          >
                            <Power className="w-3.5 h-3.5" />
                            {u.isActive ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            disabled={busy || u.isActive}
                            onClick={() => setPendingDelete(u)}
                            title={
                              u.isActive ? 'Deactivate before deleting' : 'Delete user'
                            }
                            className="inline-flex items-center justify-center rounded-md border border-red-200 p-1.5 text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete confirmation */}
      <Dialog open={!!pendingDelete} onOpenChange={(o) => !o && setPendingDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete user</DialogTitle>
            <DialogDescription>
              This permanently removes{' '}
              <span className="font-semibold text-gray-900">{pendingDelete?.name}</span> (
              {pendingDelete?.email}). This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              onClick={() => setPendingDelete(null)}
              className="inline-flex items-center justify-center rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              disabled={deleteMutation.isPending}
              onClick={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
              className="inline-flex items-center gap-1.5 justify-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              {deleteMutation.isPending ? 'Deleting…' : 'Delete user'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
