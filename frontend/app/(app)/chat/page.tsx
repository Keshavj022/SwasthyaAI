'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/hooks/useAuth'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { PatientContextPanel } from '@/components/chat/PatientContextPanel'
import { patientApi, apiClient } from '@/lib/api'
import type { Patient } from '@/types'

function ChatPageInner() {
  const { user } = useAuth()
  const searchParams = useSearchParams()
  const patientId = searchParams.get('patientId') ?? undefined
  const analyzeDocId = searchParams.get('analyzeDoc') ?? undefined

  const showContextPanel = user?.role === 'doctor' && !!patientId

  // Load patient summary so we can forward it as context to the orchestrator.
  const { data: patient } = useQuery<Patient>({
    queryKey: ['patient', patientId],
    queryFn: () => patientApi.getById(patientId!),
    enabled: !!patientId && user?.role === 'doctor',
  })

  const patientContext = useMemo(() => {
    if (!patient) return undefined
    return {
      patient_summary: {
        name: patient.name,
        age: patient.age,
        gender: patient.gender,
        blood_group: patient.bloodGroup,
        active_conditions: patient.activeConditions ?? [],
        current_medications: patient.currentMedications ?? [],
        allergies: patient.allergies ?? [],
      },
    }
  }, [patient])

  // Fetch a document image (routed from /documents "Analyze with AI") and hand
  // it to the chat interface to auto-send once.
  const [analyzeImage, setAnalyzeImage] = useState<
    { base64: string; mimeType: string; fileName: string } | null
  >(null)

  useEffect(() => {
    if (!analyzeDocId) return
    let cancelled = false
    ;(async () => {
      try {
        const { data, headers } = await apiClient.get(
          `/api/documents/${analyzeDocId}/download`,
          { responseType: 'blob' }
        )
        const blob = data as Blob
        const mimeType =
          (headers as Record<string, string>)['content-type'] || blob.type || 'image/jpeg'
        // Derive a filename from the content-disposition header if present.
        const dispo = (headers as Record<string, string>)['content-disposition'] ?? ''
        const match = /filename="?([^"]+)"?/i.exec(dispo)
        const fileName = match?.[1] ?? `document-${analyzeDocId}`
        const base64: string = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => {
            const r = reader.result as string
            resolve(r.includes(',') ? r.split(',')[1] : r)
          }
          reader.onerror = () => reject(new Error('read failed'))
          reader.readAsDataURL(blob)
        })
        if (!cancelled) setAnalyzeImage({ base64, mimeType, fileName })
      } catch {
        /* silently ignore — user can re-attach manually */
      }
    })()
    return () => {
      cancelled = true
    }
  }, [analyzeDocId])

  if (!user) return null

  return (
    <div className="flex h-full">
      {/* Main chat */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        <ChatInterface
          user={user}
          patientId={patientId}
          patientContext={patientContext}
          analyzeImage={analyzeImage}
          onAnalyzeConsumed={() => setAnalyzeImage(null)}
        />
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
