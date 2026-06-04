'use client'

import { useMemo } from 'react'
import {
  Server,
  Database,
  WifiOff,
  Wifi,
  RefreshCw,
  AlertTriangle,
  BrainCircuit,
  BarChart3,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import ModelStatusCard from '@/components/admin/ModelStatusCard'
import { useSystemHealth, useAIStatus } from '@/hooks/useSystemHealth'
import { useAuditLogs } from '@/hooks/useAudit'
import { cn } from '@/lib/utils'

const AGENT_COLORS: Record<string, string> = {
  triage: '#dc2626',
  diagnostic_support: '#2563eb',
  communication: '#0d9488',
  health_support: '#16a34a',
  image_analysis: '#9333ea',
  voice: '#ea580c',
  drug_info: '#0891b2',
  health_memory: '#7c3aed',
  lab_results: '#ca8a04',
}

function colorForAgent(name: string): string {
  return AGENT_COLORS[name] ?? '#64748b'
}

function prettyAgent(name: string): string {
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

interface StatusDotCardProps {
  label: string
  value: string
  ok: boolean
  neutral?: boolean
  icon: React.ReactNode
}

function StatusDotCard({ label, value, ok, neutral, icon }: StatusDotCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-gray-500">{label}</p>
        <span className="text-gray-300">{icon}</span>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span
          className={cn(
            'w-2.5 h-2.5 rounded-full',
            neutral ? 'bg-teal-500' : ok ? 'bg-green-500' : 'bg-red-500',
            ok && !neutral && 'animate-pulse'
          )}
        />
        <span className="text-base font-semibold text-gray-900">{value}</span>
      </div>
    </div>
  )
}

export default function SystemHealthDashboard() {
  const { data: health, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } =
    useSystemHealth()
  const { data: ai, isLoading: aiLoading } = useAIStatus()
  // Pull a wide window of logs to summarise requests-per-agent.
  const { data: auditData } = useAuditLogs({ limit: 500 })

  const apiOk = health?.status === 'ok' || health?.status === 'healthy'
  const dbOk = health?.database?.status === 'connected' || health?.database?.status === 'ok'
  const offlineEnabled = Boolean(health?.offline_mode?.enabled)

  const chartData = useMemo(() => {
    const logs = auditData?.logs ?? []
    const counts = new Map<string, number>()
    for (const log of logs) {
      const name = log.agent_name ?? log.agentType ?? 'unknown'
      counts.set(name, (counts.get(name) ?? 0) + 1)
    }
    return Array.from(counts.entries())
      .map(([agent, count]) => ({ agent, label: prettyAgent(agent), count }))
      .sort((a, b) => b.count - a.count)
  }, [auditData])

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : '—'

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[88px] rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-40 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Unable to reach the backend</p>
            <p className="mt-1 text-sm text-red-700">
              {error?.message || 'The health endpoint did not respond. The system may be offline.'}
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
    )
  }

  return (
    <div className="space-y-6">
      {/* Refresh indicator */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-400">
          Auto-refreshes every 30s · Last updated {lastUpdated}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className={cn('w-3.5 h-3.5', isFetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Status overview cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusDotCard
          label="API Server"
          value={apiOk ? 'Healthy' : 'Down'}
          ok={apiOk}
          icon={<Server className="w-4 h-4" />}
        />
        <StatusDotCard
          label="Database"
          value={dbOk ? 'Connected' : 'Disconnected'}
          ok={dbOk}
          icon={<Database className="w-4 h-4" />}
        />
        <StatusDotCard
          label="Offline Mode"
          value={offlineEnabled ? 'Enabled' : 'Disabled'}
          ok={offlineEnabled}
          neutral={offlineEnabled}
          icon={offlineEnabled ? <WifiOff className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
        />
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-gray-500">Environment</p>
            <span className="text-gray-300">
              <BrainCircuit className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <span className="text-base font-semibold text-gray-900 capitalize">
              {health?.environment || 'unknown'}
            </span>
            <p className="text-xs text-gray-400 mt-0.5">
              v{health?.version || '—'} · {health?.application || 'SwasthyaAI'}
            </p>
          </div>
        </div>
      </div>

      {/* AI model status grid */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-gray-900">AI Model Status</h2>
          {ai && !ai.anyLoaded && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              No models loaded — demo mode
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
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
            <EmptyState
              icon={<BrainCircuit className="w-6 h-6" />}
              title="No model information"
              description="The AI status endpoint reported no models. They may not be configured on this server."
              className="py-10"
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {ai!.models.map((m) => (
              <ModelStatusCard key={m.name} model={m} />
            ))}
          </div>
        )}
      </section>

      {/* Requests per agent chart */}
      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-gray-900">Requests by Agent</h2>
          <span className="text-xs text-gray-400">(recent audit activity)</span>
        </div>
        {chartData.length === 0 ? (
          <EmptyState
            icon={<BarChart3 className="w-6 h-6" />}
            title="No agent activity yet"
            description="Once agents start handling queries, request volume will appear here."
            className="py-8"
          />
        ) : (
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11 }}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                  height={60}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                  cursor={{ fill: '#f9fafb' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Requests">
                  {chartData.map((d) => (
                    <Cell key={d.agent} fill={colorForAgent(d.agent)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    </div>
  )
}
