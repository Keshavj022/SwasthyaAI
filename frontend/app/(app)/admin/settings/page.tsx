'use client'

import Link from 'next/link'
import {
  Settings as SettingsIcon,
  WifiOff,
  Wifi,
  Database,
  ShieldCheck,
  BrainCircuit,
  ChevronRight,
  Info,
} from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import PageHeader from '@/components/ui/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import ModelStatusCard from '@/components/admin/ModelStatusCard'
import { useSystemHealth, useAIStatus } from '@/hooks/useSystemHealth'
import { cn } from '@/lib/utils'

function ConfigRow({
  label,
  value,
  ok,
  neutral,
}: {
  label: string
  value: string
  ok?: boolean
  neutral?: boolean
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="flex items-center gap-2 text-sm font-medium text-gray-900">
        {ok !== undefined && (
          <span
            className={cn(
              'w-2 h-2 rounded-full',
              neutral ? 'bg-teal-500' : ok ? 'bg-green-500' : 'bg-red-500'
            )}
          />
        )}
        {value}
      </span>
    </div>
  )
}

function SettingsInner() {
  const { data: health, isLoading } = useSystemHealth()
  const { data: ai, isLoading: aiLoading } = useAIStatus()

  const offlineEnabled = Boolean(health?.offline_mode?.enabled)
  const dbOk = health?.database?.status === 'connected' || health?.database?.status === 'ok'

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title="Settings"
        subtitle="System configuration overview"
        breadcrumb={[{ label: 'Admin', href: '/dashboard/admin' }, { label: 'Settings' }]}
      />

      <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
        <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <p className="text-sm text-blue-800">
          These settings reflect the server&apos;s runtime configuration. Values are managed via the
          backend environment and are read-only here.
        </p>
      </div>

      {/* Environment & data */}
      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-2">
          <SettingsIcon className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-gray-900">Environment</h2>
        </div>
        {isLoading ? (
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </div>
        ) : (
          <div>
            <ConfigRow label="Application" value={health?.application || 'SwasthyaAI'} />
            <ConfigRow label="Version" value={`v${health?.version || '—'}`} />
            <ConfigRow
              label="Environment"
              value={health?.environment || 'unknown'}
            />
            <ConfigRow
              label="Database"
              value={dbOk ? 'Connected' : 'Disconnected'}
              ok={dbOk}
            />
            <ConfigRow
              label="Database type"
              value={health?.database?.type || '—'}
            />
            <ConfigRow
              label="Offline mode"
              value={offlineEnabled ? 'Enabled' : 'Disabled'}
              ok={offlineEnabled}
              neutral={offlineEnabled}
            />
          </div>
        )}
      </section>

      {/* AI models */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-gray-900">AI Models</h2>
          {ai && !ai.anyLoaded && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              Demo mode — no models loaded
            </span>
          )}
        </div>
        {aiLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
        ) : (ai?.models?.length ?? 0) === 0 ? (
          <p className="text-sm text-gray-500 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            No model configuration reported by the server.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {ai!.models.map((m) => (
              <ModelStatusCard key={m.name} model={m} />
            ))}
          </div>
        )}
      </section>

      {/* Quick links */}
      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Administration</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <QuickLink
            href="/admin/users"
            icon={<ShieldCheck className="w-4 h-4" />}
            title="User management"
            desc="Roles, activation, deletion"
          />
          <QuickLink
            href="/admin/system"
            icon={<Database className="w-4 h-4" />}
            title="System health"
            desc="Infrastructure and model status"
          />
          <QuickLink
            href="/admin/audit"
            icon={offlineEnabled ? <WifiOff className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
            title="Audit logs"
            desc="AI decisions and reasoning trail"
          />
          <QuickLink
            href="/admin/appointments"
            icon={<SettingsIcon className="w-4 h-4" />}
            title="All appointments"
            desc="Hospital-wide schedule"
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
      className="flex items-center gap-3 rounded-lg border border-gray-100 p-3 hover:border-teal-200 hover:bg-teal-50/40 transition-colors group"
    >
      <span className="w-9 h-9 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center shrink-0">
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

export default function AdminSettingsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <SettingsInner />
      </div>
    </ProtectedRoute>
  )
}
