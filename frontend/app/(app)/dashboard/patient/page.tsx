'use client'

import { useMemo, useState } from 'react'
import { Calendar, Pill, Flame, MessageCircle } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import StatCard from '@/components/ui/StatCard'
import WelcomeBanner from '@/components/patient/WelcomeBanner'
import DailyCheckInCard from '@/components/patient/DailyCheckInCard'
import UpcomingAppointments from '@/components/patient/UpcomingAppointments'
import HealthTrendsChart from '@/components/patient/HealthTrendsChart'
import MedicationReminders from '@/components/patient/MedicationReminders'
import RecentAIChats from '@/components/patient/RecentAIChats'
import { useAuth } from '@/hooks/useAuth'
import { useMyAppointments } from '@/hooks/useAppointments'
import { useHealthHistory } from '@/hooks/usePatients'
import type { HealthCheckIn } from '@/types'

const CHAT_KEY = 'swasthya_chat_history'

function getAIQueryCount(): number {
  try {
    const raw = typeof window !== 'undefined' ? localStorage.getItem(CHAT_KEY) : null
    if (!raw) return 0
    const msgs: { role: string; timestamp: string }[] = JSON.parse(raw)
    const now = new Date()
    return msgs.filter((m) => {
      if (m.role !== 'user') return false
      const d = new Date(m.timestamp)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    }).length
  } catch {
    return 0
  }
}

function getStreak(history: HealthCheckIn[]): number {
  if (!history.length) return 0
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let streak = 0
  const check = new Date(today)
  const dateSet = new Set(
    history.map((h) => {
      const d = new Date(h.timestamp)
      d.setHours(0, 0, 0, 0)
      return d.getTime()
    })
  )
  while (dateSet.has(check.getTime())) {
    streak++
    check.setDate(check.getDate() - 1)
  }
  return streak
}

function isTodayCheckedIn(history: HealthCheckIn[]): boolean {
  const today = new Date()
  return history.some((h) => {
    const d = new Date(h.timestamp)
    return (
      d.getDate() === today.getDate() &&
      d.getMonth() === today.getMonth() &&
      d.getFullYear() === today.getFullYear()
    )
  })
}

function PatientDashboardInner() {
  const { user } = useAuth()
  const patientId = user?.id ?? ''

  const { data: appointments } = useMyAppointments(patientId)
  const { data: history } = useHealthHistory(patientId)

  const [checkInDismissed, setCheckInDismissed] = useState(false)

  const checkedInToday = useMemo(
    () => isTodayCheckedIn(history ?? []),
    [history]
  )
  const showCheckIn = !checkedInToday && !checkInDismissed

  const upcomingCount = useMemo(
    () =>
      (appointments ?? []).filter(
        (a) =>
          a.status !== 'cancelled' &&
          a.status !== 'completed' &&
          new Date(a.dateTime) >= new Date()
      ).length,
    [appointments]
  )

  const streak = useMemo(() => getStreak(history ?? []), [history])
  const aiQueries = getAIQueryCount()

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome banner */}
      <WelcomeBanner checkInDoneToday={checkedInToday} />

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Appointments"
          value={upcomingCount}
          subtitle="This week"
          icon={<Calendar className="w-5 h-5" />}
          color="teal"
        />
        <StatCard
          title="Medications"
          value={3}
          subtitle="Due today"
          icon={<Pill className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Check-in Streak"
          value={streak}
          subtitle={streak === 1 ? 'day' : 'days'}
          icon={<Flame className="w-5 h-5" />}
          color="amber"
        />
        <StatCard
          title="AI Queries"
          value={aiQueries}
          subtitle="This month"
          icon={<MessageCircle className="w-5 h-5" />}
          color="green"
        />
      </div>

      {/* Daily check-in prompt */}
      {showCheckIn && (
        <DailyCheckInCard onSuccess={() => setCheckInDismissed(true)} />
      )}

      {/* Main grid: appointments + AI chats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <UpcomingAppointments patientId={patientId} />
        <RecentAIChats />
      </div>

      {/* Bottom grid: trends + medications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <HealthTrendsChart patientId={patientId} />
        <MedicationReminders />
      </div>
    </div>
  )
}

export default function PatientDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <PatientDashboardInner />
    </ProtectedRoute>
  )
}
