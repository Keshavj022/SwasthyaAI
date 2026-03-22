'use client'

import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import {
  useAdminUsers,
  useUpdateAdminUser,
  useDeleteAdminUser,
  useCreateAdminUser,
  useResetAdminPassword,
} from '@/hooks/useAdmin'
import * as Dialog from '@radix-ui/react-dialog'
import { X, UserPlus, Shield, Stethoscope, User, MoreHorizontal, KeyRound, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import type { AdminUser } from '@/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ROLE_CONFIG: Record<string, { label: string; cls: string }> = {
  admin:   { label: 'Admin',   cls: 'bg-purple-100 text-purple-700' },
  doctor:  { label: 'Doctor',  cls: 'bg-teal-100 text-teal-700'    },
  patient: { label: 'Patient', cls: 'bg-blue-100 text-blue-700'    },
}

function RoleBadge({ role }: { role: string }) {
  const cfg = ROLE_CONFIG[role] ?? { label: role, cls: 'bg-gray-100 text-gray-600' }
  const Icon = role === 'admin' ? Shield : role === 'doctor' ? Stethoscope : User
  return (
    <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-medium w-fit ${cfg.cls}`}>
      <Icon size={10} aria-hidden="true" />
      {cfg.label}
    </span>
  )
}

function safeDate(raw: string | null | undefined): string {
  if (!raw) return '—'
  try { return format(parseISO(raw), 'd MMM yyyy') } catch { return raw }
}

// ---------------------------------------------------------------------------
// Add User dialog
// ---------------------------------------------------------------------------

function AddUserDialog({ onClose }: { onClose: () => void }) {
  const { mutate: createUser, isPending } = useCreateAdminUser()
  const [form, setForm] = useState({ email: '', password: '', fullName: '', role: 'patient' })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.email || !form.password || !form.fullName) {
      toast.error('All fields are required')
      return
    }
    createUser(form, {
      onSuccess: () => { toast.success('User created'); onClose() },
      onError: (err) => toast.error(err.message ?? 'Failed to create user'),
    })
  }

  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40" />
      <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-xl w-full max-w-md p-6 z-50">
        <div className="flex items-center justify-between mb-4">
          <Dialog.Title className="font-semibold text-gray-900">Add New User</Dialog.Title>
          <Dialog.Close asChild>
            <button type="button" className="text-gray-400 hover:text-gray-600" aria-label="Close dialog">
              <X size={18} aria-hidden="true" />
            </button>
          </Dialog.Close>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="add-user-name" className="block text-xs font-medium text-gray-700 mb-1">Full Name</label>
            <input
              id="add-user-name"
              type="text"
              value={form.fullName}
              onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
              placeholder="Dr. Jane Smith"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300"
            />
          </div>
          <div>
            <label htmlFor="add-user-email" className="block text-xs font-medium text-gray-700 mb-1">Email</label>
            <input
              id="add-user-email"
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              placeholder="jane@hospital.org"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300"
            />
          </div>
          <div>
            <label htmlFor="add-user-password" className="block text-xs font-medium text-gray-700 mb-1">Password</label>
            <input
              id="add-user-password"
              type="password"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              placeholder="Minimum 8 characters"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300"
            />
          </div>
          <div>
            <label htmlFor="add-user-role" className="block text-xs font-medium text-gray-700 mb-1">Role</label>
            <select
              id="add-user-role"
              value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300 bg-white"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Dialog.Close asChild>
              <button
                type="button"
                className="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </Dialog.Close>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 text-sm rounded-xl bg-teal-600 text-white font-medium hover:bg-teal-700 disabled:opacity-50"
            >
              {isPending ? 'Creating…' : 'Create User'}
            </button>
          </div>
        </form>
      </Dialog.Content>
    </Dialog.Portal>
  )
}

// ---------------------------------------------------------------------------
// Row actions menu
// ---------------------------------------------------------------------------

function RowActions({ user }: { user: AdminUser }) {
  const [open, setOpen] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const deleteTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { mutate: updateUser, isPending: updating } = useUpdateAdminUser()
  const { mutate: deleteUser, isPending: deleting } = useDeleteAdminUser()
  const { mutate: resetPwd, isPending: resetting } = useResetAdminPassword()

  // Cleanup timer on unmount to prevent stale state updates
  useEffect(() => {
    return () => {
      if (deleteTimerRef.current) clearTimeout(deleteTimerRef.current)
    }
  }, [])

  function closeMenu() { setOpen(false) }

  function toggleActive() {
    updateUser(
      { userId: user.id, patch: { isActive: !user.isActive } },
      {
        onSuccess: () => toast.success(user.isActive ? 'User deactivated' : 'User activated'),
        onError: () => toast.error('Failed to update user'),
      }
    )
    closeMenu()
  }

  function changeRole(role: string) {
    updateUser(
      { userId: user.id, patch: { role } },
      {
        onSuccess: () => toast.success(`Role changed to ${role}`),
        onError: () => toast.error('Failed to update role'),
      }
    )
    closeMenu()
  }

  function handleReset() {
    resetPwd(user.id, {
      onSuccess: (data) => {
        toast.success(`Temp password: ${data.tempPassword}`, { duration: 10000 })
        closeMenu()
      },
      onError: () => toast.error('Failed to reset password'),
    })
  }

  function handleDelete() {
    if (!deleteConfirm) {
      setDeleteConfirm(true)
      deleteTimerRef.current = setTimeout(() => setDeleteConfirm(false), 4000)
      return
    }
    if (deleteTimerRef.current) clearTimeout(deleteTimerRef.current)
    deleteUser(user.id, {
      onSuccess: () => { toast.success('User deleted'); closeMenu() },
      onError: (err) => toast.error(err.message ?? 'Failed to delete user'),
    })
  }

  const otherRoles = (['patient', 'doctor', 'admin'] as const).filter((r) => r !== user.role)

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
        aria-label={`Actions for ${user.fullName}`}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <MoreHorizontal size={16} aria-hidden="true" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className="absolute right-0 top-8 z-20 bg-white border border-gray-200 rounded-xl shadow-lg py-1 w-48" role="menu">
            {/* Toggle active */}
            <button
              type="button"
              role="menuitem"
              onClick={toggleActive}
              disabled={updating}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {user.isActive ? <ToggleLeft size={14} aria-hidden="true" /> : <ToggleRight size={14} aria-hidden="true" />}
              {user.isActive ? 'Deactivate' : 'Activate'}
            </button>

            {/* Change role */}
            <div className="px-3 py-1.5 border-t border-gray-100">
              <p className="text-[10px] text-gray-400 mb-1 uppercase tracking-wide">Change role to</p>
              {otherRoles.map((r) => (
                <button
                  key={r}
                  type="button"
                  role="menuitem"
                  onClick={() => changeRole(r)}
                  disabled={updating}
                  className="w-full flex items-center gap-2 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50 rounded disabled:opacity-50"
                >
                  {ROLE_CONFIG[r]?.label ?? r}
                </button>
              ))}
            </div>

            {/* Reset password */}
            <div className="border-t border-gray-100">
              <button
                type="button"
                role="menuitem"
                onClick={handleReset}
                disabled={resetting}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                <KeyRound size={14} aria-hidden="true" />
                {resetting ? 'Resetting…' : 'Reset Password'}
              </button>
            </div>

            {/* Delete */}
            <div className="border-t border-gray-100">
              <button
                type="button"
                role="menuitem"
                onClick={handleDelete}
                disabled={deleting || user.isActive}
                title={user.isActive ? 'Deactivate the user before deleting' : undefined}
                className={`w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-red-50 disabled:opacity-40 ${
                  deleteConfirm ? 'text-red-700 font-semibold' : 'text-red-500'
                }`}
              >
                <Trash2 size={14} aria-hidden="true" />
                {deleteConfirm ? 'Confirm delete?' : 'Delete'}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Filter types
// ---------------------------------------------------------------------------

type RoleFilter = 'all' | 'doctor' | 'patient' | 'admin'
type StatusFilter = 'all' | 'active' | 'inactive'

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function UserTable() {
  const { data: users, isLoading, error } = useAdminUsers()
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [search, setSearch] = useState('')
  const [addOpen, setAddOpen] = useState(false)

  const filtered = (users ?? []).filter((u) => {
    if (roleFilter !== 'all' && u.role !== roleFilter) return false
    if (statusFilter === 'active' && !u.isActive) return false
    if (statusFilter === 'inactive' && u.isActive) return false
    if (search) {
      const q = search.toLowerCase()
      if (!u.fullName.toLowerCase().includes(q) && !u.email.toLowerCase().includes(q)) return false
    }
    return true
  })

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or email…"
            aria-label="Search users by name or email"
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 w-48 focus:outline-none focus:ring-2 focus:ring-teal-300"
          />
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as RoleFilter)}
            aria-label="Filter by role"
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
          >
            <option value="all">All roles</option>
            <option value="doctor">Doctors</option>
            <option value="patient">Patients</option>
            <option value="admin">Admins</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            aria-label="Filter by status"
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        <Dialog.Root open={addOpen} onOpenChange={setAddOpen}>
          <Dialog.Trigger asChild>
            <button
              type="button"
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700"
            >
              <UserPlus size={13} aria-hidden="true" />
              Add User
            </button>
          </Dialog.Trigger>
          <AddUserDialog onClose={() => setAddOpen(false)} />
        </Dialog.Root>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" aria-label="User management table">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              {['Name', 'Email', 'Role', 'Status', 'Created', 'Actions'].map((h) => (
                <th key={h} className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">Loading users…</td></tr>
            )}
            {error && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-red-500 text-sm">Failed to load users.</td></tr>
            )}
            {!isLoading && !error && filtered.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">No users match the current filters.</td></tr>
            )}
            {filtered.map((user) => (
              <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.fullName}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{user.email}</td>
                <td className="px-4 py-3"><RoleBadge role={user.role} /></td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                    user.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {user.isActive ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">{safeDate(user.createdAt)}</td>
                <td className="px-4 py-3">
                  <RowActions user={user} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400">
        Showing {filtered.length} of {(users ?? []).length} users
      </div>
    </div>
  )
}
