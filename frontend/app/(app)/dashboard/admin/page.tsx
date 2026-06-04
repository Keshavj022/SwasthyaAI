'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  Users,
  Stethoscope,
  UserRound,
  CalendarDays,
  FileText,
  ScrollText,
  BrainCircuit,
  ShieldCheck,
  Database,
  ChevronRight,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import StatCard from '@/components/ui/StatCard'
import { Skeleton } from '@/components/ui/skeleton'
import { adminApi } from '@/lib/api'
import { useAIStatus } from '@/hooks/useSystemHealth'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import type { SystemStats } from '@/types'

function AdminDashboardInner() {
  const { user } = useAuth()

  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
    error,
    refetch,
  } = useQuery<SystemStats, Error>({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
  })

  const { data: ai, isLoading: aiLoading } = useAIStatus()

  const stubCount = (ai?.models ?? []).filter((m) => m.enabled && (!m.loaded || m.stub)).length
  const loadedCount = (ai?.models ?? []).filter((m) => m.enabled && m.loaded && !m.stub).length

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {user?.name ?? 'Administrator'}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">System administration overview</p>
      </div>

      {/* AI demo-mode banner */}
      {!aiLoading && ai && !ai.anyLoaded && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800">
            <span className="font-semibold">AI models not loaded — demo mode.</span> Agent outputs
            are illustrative stubs, not real model inferences. Review the{' '}
            <Link href="/admin/system" className="underline font-medium">
              system health page
            </Link>{' '}
            for details.
          </p>
        </div>
      )}

      {/* Stats */}
      {statsError ? (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Could not load system stats</p>
            <p className="mt-1 text-sm text-red-700">{error?.message || 'Request failed.'}</p>
            <button
              onClick={() => refetch()}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          </div>
        </div>
      ) : statsLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-[108px] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Users"
            value={stats?.totalUsers ?? 0}
            subtitle="All accounts"
            icon={<Users className="w-5 h-5" />}
            color="teal"
          />
          <StatCard
            title="Patients"
            value={stats?.totalPatients ?? 0}
            subtitle="Registered patients"
            icon={<UserRound className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            title="Doctors"
            value={stats?.totalDoctors ?? 0}
            subtitle="Active providers"
            icon={<Stethoscope className="w-5 h-5" />}
            color="green"
          />
          <StatCard
            title="Appointments"
            value={stats?.totalAppointments ?? 0}
            subtitle="All time"
            icon={<CalendarDays className="w-5 h-5" />}
            color="amber"
          />
          <StatCard
            title="Documents"
            value={stats?.totalDocuments ?? 0}
            subtitle="Stored files"
            icon={<FileText className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            title="Audit Logs"
            value={stats?.totalAuditLogs ?? 0}
            subtitle="Total entries"
            icon={<ScrollText className="w-5 h-5" />}
            color="teal"
          />
          <StatCard
            title="AI Queries Today"
            value={stats?.aiQueriesToday ?? 0}
            subtitle="Since midnight"
            icon={<BrainCircuit className="w-5 h-5" />}
            color="green"
          />
          <StatCard
            title="Models Live"
            value={aiLoading ? '…' : `${loadedCount}/${ai?.models?.length ?? 0}`}
            subtitle={stubCount > 0 ? `${stubCount} in stub mode` : 'All loaded'}
            icon={<BrainCircuit className="w-5 h-5" />}
            color={stubCount > 0 ? 'amber' : 'green'}
          />
        </div>
      )}

      {/* Quick links */}
      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Quick actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <QuickLink
            href="/admin/users"
            icon={<ShieldCheck className="w-5 h-5" />}
            title="Manage users"
            desc="Roles, activation, deletion"
          />
          <QuickLink
            href="/admin/audit"
            icon={<ScrollText className="w-5 h-5" />}
            title="Audit logs"
            desc="AI decisions and reasoning"
          />
          <QuickLink
            href="/admin/system"
            icon={<Database className="w-5 h-5" />}
            title="System health"
            desc="Infrastructure & models"
          />
          <QuickLink
            href="/admin/appointments"
            icon={<CalendarDays className="w-5 h-5" />}
            title="All appointments"
            desc="Hospital-wide schedule"
          />
          <QuickLink
            href="/admin/settings"
            icon={<BrainCircuit className="w-5 h-5" />}
            title="Settings"
            desc="Configuration overview"
          />
        </div>
      </section>
    </div>
  )
}

function QuickLink({
  href,
  icon,
  title,
  desc,
}: {
  href: string
  icon: React.ReactNode
  title: string
  desc: string
}) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 rounded-lg border border-gray-100 p-3.5',
        'hover:border-teal-200 hover:bg-teal-50/40 transition-colors group'
      )}
    >
      <span className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center shrink-0">
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{title}</p>
        <p className="text-xs text-gray-500 truncate">{desc}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-teal-500 transition-colors" />
    </Link>
  )
}

export default function AdminDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <AdminDashboardInner />
      </div>
    </ProtectedRoute>
  )
}
