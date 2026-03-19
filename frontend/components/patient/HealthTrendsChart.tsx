'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Activity } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import { useHealthHistory } from '@/hooks/usePatients'
import type { HealthCheckIn } from '@/types'

const DAY_ABBR = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function toChartData(checkIns: HealthCheckIn[]) {
  return [...checkIns]
    .reverse()
    .map((c) => ({
      day: DAY_ABBR[new Date(c.timestamp).getDay()],
      Mood: c.mood ?? null,
      Energy: c.energy ?? null,
      Sleep: c.sleep ?? null,
    }))
}

interface Props {
  patientId: string
}

export default function HealthTrendsChart({ patientId }: Props) {
  const { data: history, isLoading } = useHealthHistory(patientId)

  if (isLoading) {
    return <Skeleton className="h-56 w-full rounded-2xl" />
  }

  const chartData = toChartData(history ?? [])

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <h2 className="text-base font-semibold text-gray-900 mb-4">Health Trends (7 days)</h2>

      {chartData.length < 2 ? (
        <EmptyState
          icon={<Activity className="w-6 h-6" />}
          title="Not enough data yet"
          description="Complete daily check-ins to see your health trends."
          className="py-8"
        />
      ) : (
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="Mood" stroke="#14b8a6" strokeWidth={2} dot={false} connectNulls />
              <Line type="monotone" dataKey="Energy" stroke="#3b82f6" strokeWidth={2} dot={false} connectNulls />
              <Line type="monotone" dataKey="Sleep" stroke="#8b5cf6" strokeWidth={2} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
