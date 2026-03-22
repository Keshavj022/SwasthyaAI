'use client'

import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAdminAppointments } from '@/hooks/useAdmin'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  scheduled:  'bg-blue-100 text-blue-700',
  confirmed:  'bg-teal-100 text-teal-700',
  completed:  'bg-green-100 text-green-700',
  cancelled:  'bg-red-100 text-red-700',
  pending:    'bg-yellow-100 text-yellow-700',
}

function safeDate(raw: string) {
  try { return format(parseISO(raw), 'd MMM yyyy, HH:mm') } catch { return raw }
}

const PAGE_SIZE = 20

function AppointmentsPageInner() {
  const [page, setPage] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [specialtyFilter, setSpecialtyFilter] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const { data, isLoading, error } = useAdminAppointments({
    status: statusFilter || undefined,
    specialty: specialtyFilter || undefined,
    fromDate: fromDate || undefined,
    toDate: toDate || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  })

  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function resetFilters() {
    setStatusFilter('')
    setSpecialtyFilter('')
    setFromDate('')
    setToDate('')
    setPage(0)
  }

  const hasFilters = statusFilter || specialtyFilter || fromDate || toDate

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">All Appointments</h1>
        <p className="text-sm text-gray-500 mt-1">Read-only view of all appointments in the system.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0) }}
          aria-label="Filter by status"
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-300"
        >
          <option value="">All statuses</option>
          {['scheduled', 'confirmed', 'completed', 'cancelled', 'pending'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input
          type="text"
          value={specialtyFilter}
          onChange={(e) => { setSpecialtyFilter(e.target.value); setPage(0) }}
          placeholder="Specialty…"
          aria-label="Filter by specialty"
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 w-36 focus:outline-none focus:ring-2 focus:ring-teal-300"
        />
        <input
          type="date"
          value={fromDate}
          onChange={(e) => { setFromDate(e.target.value); setPage(0) }}
          aria-label="From date"
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-300"
        />
        <input
          type="date"
          value={toDate}
          onChange={(e) => { setToDate(e.target.value); setPage(0) }}
          aria-label="To date"
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-300"
        />
        {hasFilters && (
          <button
            type="button"
            onClick={resetFilters}
            className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded border border-gray-200 bg-white"
          >
            Reset
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-gray-50">
          <span className="text-xs text-gray-500">
            {isLoading ? 'Loading…' : `${total.toLocaleString()} appointments`}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded border border-gray-200 disabled:opacity-40 hover:bg-white"
              aria-label="Previous page"
            >
              <ChevronLeft size={14} aria-hidden="true" />
            </button>
            <span className="text-xs text-gray-500 w-20 text-center" aria-live="polite">
              {page + 1} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded border border-gray-200 disabled:opacity-40 hover:bg-white"
              aria-label="Next page"
            >
              <ChevronRight size={14} aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm" aria-label="All appointments">
            <thead>
              <tr className="border-b border-gray-100 bg-white">
                {['Patient', 'Doctor', 'Date/Time', 'Type', 'Status'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">Loading…</td></tr>
              )}
              {error && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-red-500 text-sm">Failed to load appointments.</td></tr>
              )}
              {!isLoading && !error && (data?.appointments ?? []).length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No appointments found.</td></tr>
              )}
              {(data?.appointments ?? []).map((appt) => (
                <tr key={appt.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-2.5 text-xs font-mono text-gray-500">{appt.patientId}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-700">{appt.doctorName ?? appt.doctorId ?? '—'}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-600 whitespace-nowrap">{safeDate(appt.dateTime)}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-500">{appt.type ?? '—'}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[appt.status] ?? 'bg-gray-100 text-gray-600'}`}>
                      {appt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default function AdminAppointmentsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AppointmentsPageInner />
    </ProtectedRoute>
  )
}
