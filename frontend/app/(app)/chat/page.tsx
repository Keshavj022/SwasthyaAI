'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/hooks/useAuth'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { PatientContextPanel } from '@/components/chat/PatientContextPanel'

function ChatPageInner() {
  const { user } = useAuth()
  const searchParams = useSearchParams()
  const patientId = searchParams.get('patientId') ?? undefined

  // Doctor can pass ?patientId=xxx to get context panel
  const showContextPanel = user?.role === 'doctor' && !!patientId

  if (!user) return null

  return (
    <div className="flex h-full">
      {/* Main chat */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        <ChatInterface user={user} patientId={patientId} />
      </div>

      {/* Doctor patient context panel */}
      {showContextPanel && <PatientContextPanel patientId={patientId!} />}
    </div>
  )
}

export default function ChatPage() {
  return (
    <ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']}>
      <Suspense>
        <ChatPageInner />
      </Suspense>
    </ProtectedRoute>
  )
}
