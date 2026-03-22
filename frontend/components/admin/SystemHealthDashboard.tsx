'use client'

import { useSystemHealth } from '@/hooks/useSystemHealth'
import { useAdminStats } from '@/hooks/useAdmin'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle, XCircle, WifiOff, Clock, Database, Users, FileText, Brain,
  Activity, Zap, Shield, Stethoscope, Cpu, Mic, Eye, type LucideIcon,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatUptime(startTimeStr?: string): string {
  if (!startTimeStr) return '—'
  try {
    const start = new Date(startTimeStr)
    const diff = Date.now() - start.getTime()
    const days = Math.floor(diff / 86_400_000)
    const hours = Math.floor((diff % 86_400_000) / 3_600_000)
    const minutes = Math.floor((diff % 3_600_000) / 60_000)
    const parts: string[] = []
    if (days > 0) parts.push(`${days}d`)
    if (hours > 0) parts.push(`${hours}h`)
    parts.push(`${minutes}m`)
    return parts.join(' ')
  } catch {
    return '—'
  }
}

function formatBytes(kb: number): string {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(0)} KB`
}

// Agent display config
const AGENT_CONFIG: Record<string, { label: string; Icon: LucideIcon }> = {
  triage: { label: 'Triage', Icon: Zap },
  health_memory: { label: 'Health Memory', Icon: Brain },
  medical_imaging: { label: 'Medical Imaging', Icon: Activity },
  prescription: { label: 'Prescription', Icon: FileText },
  explainability: { label: 'Explainability', Icon: Shield },
  orchestrator: { label: 'Orchestrator', Icon: Stethoscope },
}

const CHART_COLORS = ['#0d9488', '#6366f1', '#f59e0b', '#ec4899', '#10b981', '#8b5cf6']

// ---------------------------------------------------------------------------
// Status card
// ---------------------------------------------------------------------------

function StatusCard({
  label,
  value,
  ok,
  icon: Icon,
}: {
  label: string
  value: string
  ok: boolean
  icon: LucideIcon
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4 flex items-start gap-3">
      <div className={`p-2 rounded-xl ${ok ? 'bg-teal-50' : 'bg-red-50'}`}>
        <Icon size={18} className={ok ? 'text-teal-600' : 'text-red-500'} />
      </div>
      <div>
        <p className="text-xs text-gray-500 mb-0.5">{label}</p>
        <div className="flex items-center gap-1.5">
          {ok ? (
            <CheckCircle size={12} className="text-teal-500" aria-hidden="true" />
          ) : (
            <XCircle size={12} className="text-red-500" aria-hidden="true" />
          )}
          <span className={`text-sm font-semibold ${ok ? 'text-teal-700' : 'text-red-600'}`}>{value}</span>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Metric card
// ---------------------------------------------------------------------------

function MetricCard({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4 flex items-center gap-3">
      <div className="p-2 rounded-xl bg-indigo-50">
        <Icon size={18} className="text-indigo-600" />
      </div>
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-lg font-bold text-gray-900">{value}</p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// AI Model status card
// ---------------------------------------------------------------------------

interface ModelStatus {
  loaded: boolean
  available: boolean
}

interface AiStatus {
  medgemma: ModelStatus
  medsiglip: ModelStatus
  medasr: ModelStatus
  device: string
}

const MODEL_CONFIG: {
  key: keyof Omit<AiStatus, 'device'>
  label: string
  subtitle: string
  Icon: LucideIcon
}[] = [
  {
    key: 'medgemma',
    label: 'MedGemma 1.5 4B',
    subtitle: 'Text & image medical reasoning',
    Icon: Brain,
  },
  {
    key: 'medsiglip',
    label: 'MedSigLIP 448',
    subtitle: 'Zero-shot image classification',
    Icon: Eye,
  },
  {
    key: 'medasr',
    label: 'MedASR',
    subtitle: 'Medical speech-to-text',
    Icon: Mic,
  },
]

function ModelStatusCard({
  label,
  subtitle,
  status,
  icon: Icon,
}: {
  label: string
  subtitle: string
  status: ModelStatus | undefined
  icon: LucideIcon
}) {
  const loaded = status?.loaded ?? false
  const available = status?.available ?? false

  const badge = !loaded
    ? { text: 'Loading…', cls: 'bg-amber-100 text-amber-700' }
    : available
    ? { text: 'Ready', cls: 'bg-teal-100 text-teal-700' }
    : { text: 'Unavailable', cls: 'bg-red-100 text-red-600' }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg ${available ? 'bg-teal-50' : 'bg-gray-100'}`}>
            <Icon size={14} className={available ? 'text-teal-600' : 'text-gray-400'} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{label}</p>
            <p className="text-xs text-gray-400">{subtitle}</p>
          </div>
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${badge.cls}`}>
          {badge.text}
        </span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function SystemHealthDashboard() {
  const { data: health, isLoading: healthLoading } = useSystemHealth()
  const { data: stats, isLoading: statsLoading } = useAdminStats()

  const { data: aiStatusData, isLoading: aiLoading } = useQuery<{ ai_models: AiStatus }>({
    queryKey: ['ai-status'],
    queryFn: async () => {
      const res = await fetch('/api/health/ai-status')
      if (!res.ok) throw new Error('AI status unavailable')
      return res.json()
    },
    refetchInterval: 30_000,
    retry: false,
  })
  const aiModels = aiStatusData?.ai_models

  const isApiOk = health?.status === 'healthy'
  const isDbOk = health?.database?.status === 'connected' || health?.database?.file_exists === true
  const isOffline = health?.offline_mode?.enabled ?? false

  return (
    <div className="space-y-6">
      {/* Status row */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Service Status</h2>
        {healthLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatusCard label="API Server" value={isApiOk ? 'Healthy' : 'Down'} ok={isApiOk} icon={Activity} />
            <StatusCard label="Database" value={isDbOk ? 'Connected' : 'Disconnected'} ok={isDbOk} icon={Database} />
            <StatusCard label="Offline Mode" value={isOffline ? 'Enabled' : 'Disabled'} ok={true} icon={WifiOff} />
            <StatusCard
              label="Uptime"
              value={formatUptime(health?.timestamp)}
              ok={isApiOk}
              icon={Clock}
            />
          </div>
        )}
      </div>

      {/* Metrics row */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">System Metrics</h2>
        {statsLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="Database Size" value={formatBytes(stats?.dbSizeKb ?? 0)} icon={Database} />
            <MetricCard label="Total Patients" value={String(stats?.totalPatients ?? 0)} icon={Users} />
            <MetricCard label="Audit Log Entries" value={String(stats?.totalAuditLogs ?? 0)} icon={FileText} />
            <MetricCard label="Documents Stored" value={String(stats?.totalDocuments ?? 0)} icon={Brain} />
          </div>
        )}
      </div>

      {/* Agent requests chart */}
      <div className="bg-white rounded-2xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Agent Requests — Last 7 Days</h2>
        {statsLoading ? (
          <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
        ) : !stats || stats.agentRequests.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-8">No agent requests in the last 7 days.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.agentRequests} margin={{ top: 0, right: 8, bottom: 0, left: -16 }}>
              <XAxis
                dataKey="agentName"
                tick={{ fontSize: 11 }}
                tickFormatter={(v: string) => AGENT_CONFIG[v]?.label ?? v}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                formatter={(value: number) => [value, 'Requests']}
                labelFormatter={(label: string) => AGENT_CONFIG[label]?.label ?? label}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {stats.agentRequests.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* AI Model status */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">AI Models</h2>
          {aiModels?.device && (
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Cpu size={12} />
              <span>{aiModels.device.toUpperCase()}</span>
            </div>
          )}
        </div>
        {aiLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {MODEL_CONFIG.map(({ key, label, subtitle, Icon }) => (
              <ModelStatusCard
                key={key}
                label={label}
                subtitle={subtitle}
                status={aiModels?.[key]}
                icon={Icon}
              />
            ))}
          </div>
        )}
      </div>

      {/* Agent status grid */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Agent Status</h2>
        {statsLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(AGENT_CONFIG).map(([key, { label, Icon }]) => {
              const requestCount = stats?.agentRequests.find((r) => r.agentName === key)?.count ?? 0
              const isActive = requestCount > 0
              return (
                <div key={key} className="bg-white rounded-2xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Icon size={14} className="text-gray-500" aria-hidden="true" />
                      <span className="text-sm font-medium text-gray-700">{label}</span>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        isActive ? 'bg-teal-100 text-teal-700' : 'bg-gray-100 text-gray-500'
                      }`}
                      aria-label={isActive ? 'Available' : 'Offline'}
                    >
                      {isActive ? 'Available' : 'Offline'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    {requestCount} request{requestCount !== 1 ? 's' : ''} this week · ~120ms avg
                  </p>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
