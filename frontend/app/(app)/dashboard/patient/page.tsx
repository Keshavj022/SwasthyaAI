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
import { useHealthHistory, usePatient } from '@/hooks/usePatients'
import type { HealthCheckIn } from '@/types'

function getAIQueryCount(userId: string): number {
  try {
    const key = `swasthya_chat_${userId}`
    const raw = typeof window !== 'undefined' ? localStorage.getItem(key) : null
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

/** Start (Mon 00:00) and end (Sun 23:59) of the current calendar week. */
function currentWeekBounds(): { start: Date; end: Date } {
  const now = new Date()
  const day = now.getDay() // 0 = Sun
  const mondayOffset = day === 0 ? -6 : 1 - day
  const start = new Date(now)
  start.setDate(now.getDate() + mondayOffset)
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  end.setHours(23, 59, 59, 999)
  return { start, end }
}

function PatientDashboardInner() {
  const { user } = useAuth()
  const patientId = user?.id ?? ''

  const { data: appointments } = useMyAppointments(patientId)
  const { data: history } = useHealthHistory(patientId)
  const { data: patient } = usePatient(patientId)

  const [checkInDismissed, setCheckInDismissed] = useState(false)

  const checkedInToday = useMemo(() => isTodayCheckedIn(history ?? []), [history])
  const showCheckIn = !checkedInToday && !checkInDismissed

  // Appointments this week (Mon–Sun), excluding cancelled/completed.
  const weekCount = useMemo(() => {
    const { start, end } = currentWeekBounds()
    return (appointments ?? []).filter((a) => {
      if (a.status === 'cancelled' || a.status === 'completed') return false
      const d = new Date(a.dateTime)
      return d >= start && d <= end
    }).length
  }, [appointments])

  // Medications due today: count from the real patient record when present,
  // otherwise fall back to the labelled sample count (3).
  const medsCount = patient?.currentMedications?.length ?? 3
  const medsIsSample = !(patient?.currentMedications && patient.currentMedications.length > 0)

  const streak = useMemo(() => getStreak(history ?? []), [history])
  const aiQueries = getAIQueryCount(user?.id ?? '')

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Welcome banner */}
        <WelcomeBanner checkInDoneToday={checkedInToday} />

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Appointments"
            value={weekCount}
            subtitle="This week"
            icon={<Calendar className="w-5 h-5" />}
            color="teal"
          />
          <StatCard
            title="Medications"
            value={medsCount}
            subtitle={medsIsSample ? 'Sample · due today' : 'Due today'}
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
        {showCheckIn && <DailyCheckInCard onSuccess={() => setCheckInDismissed(true)} />}

        {/* Main grid: appointments + AI chats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <UpcomingAppointments patientId={patientId} />
          <RecentAIChats />
        </div>

        {/* Bottom grid: trends + medications */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <HealthTrendsChart patientId={patientId} />
          <MedicationReminders patientId={patientId} />
        </div>
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
