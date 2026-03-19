'use client'

import { useState } from 'react'
import { Calendar, FileText, AlertTriangle, Brain } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import StatCard from '@/components/ui/StatCard'
import TodaySchedule from '@/components/doctor/TodaySchedule'
import PatientQueue from '@/components/doctor/PatientQueue'
import QuickDiagnosticTool from '@/components/doctor/QuickDiagnosticTool'
import DrugInteractionChecker from '@/components/doctor/DrugInteractionChecker'
import CriticalAlerts from '@/components/doctor/CriticalAlerts'
import RecentConsultations from '@/components/doctor/RecentConsultations'
import PatientSheet from '@/components/doctor/PatientSheet'
import { useAuth } from '@/hooks/useAuth'
import { useDoctorAppointments } from '@/hooks/useAppointments'
import type { Appointment } from '@/types'
import { isToday } from '@/lib/utils'

function formatDate(): string {
  return new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function DoctorDashboardInner() {
  const { user } = useAuth()
  const doctorId = user?.id ?? ''

  const { data: appointments = [], isLoading } = useDoctorAppointments(doctorId)

  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null)
  const [sheetOpen, setSheetOpen] = useState(false)

  const todayCount = appointments.filter(
    (a) => a.status !== 'cancelled' && isToday(a.dateTime)
  ).length

  const handleSelectAppt = (appt: Appointment) => {
    setSelectedAppt(appt)
    setSheetOpen(true)
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Dr. {user?.name ?? 'Doctor'}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Physician · {formatDate()}
        </p>
      </div>

      {/* Critical alerts */}
      <CriticalAlerts />

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Today's Patients"
          value={todayCount}
          subtitle="Scheduled"
          icon={<Calendar className="w-5 h-5" />}
          color="teal"
        />
        {/* TODO: fetch real count */}
        <StatCard
          title="Pending Reports"
          value={2}
          subtitle="Awaiting review"
          icon={<FileText className="w-5 h-5" />}
          color="amber"
        />
        {/* TODO: fetch real count */}
        <StatCard
          title="Critical Alerts"
          value={0}
          subtitle="Last 24 hours"
          icon={<AlertTriangle className="w-5 h-5" />}
          color="red"
        />
        {/* TODO: fetch real count */}
        <StatCard
          title="AI Queries"
          value={0}
          subtitle="Today"
          icon={<Brain className="w-5 h-5" />}
          color="blue"
        />
      </div>

      {/* Today's schedule */}
      <TodaySchedule
        appointments={appointments}
        isLoading={isLoading}
        onSelect={handleSelectAppt}
      />

      {/* Patient queue + Quick diagnostic */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <PatientQueue appointments={appointments} isLoading={isLoading} />
        <QuickDiagnosticTool />
      </div>

      {/* Recent consultations + Drug checker */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <RecentConsultations />
        <DrugInteractionChecker />
      </div>

      {/* Patient slide-over */}
      <PatientSheet
        appointment={selectedAppt}
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
      />
    </div>
  )
}

export default function DoctorDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <DoctorDashboardInner />
    </ProtectedRoute>
  )
}
