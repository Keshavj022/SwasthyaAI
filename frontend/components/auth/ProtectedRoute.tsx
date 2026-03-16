'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

const DASHBOARD: Record<string, string> = {
  patient: '/dashboard/patient',
  doctor: '/dashboard/doctor',
  admin: '/dashboard/admin',
}

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: ('doctor' | 'patient' | 'admin')[]
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter()
  const { isAuthenticated, user } = useAuth()

  useEffect(() => {
    if (!isAuthenticated || !user) {
      router.replace('/login')
      return
    }

    if (allowedRoles && user.role && !allowedRoles.includes(user.role as 'doctor' | 'patient' | 'admin')) {
      router.replace(DASHBOARD[user.role] ?? '/login')
    }
  }, [isAuthenticated, user, allowedRoles, router])

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="space-y-3 w-48">
          <div className="h-4 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2" />
        </div>
      </div>
    )
  }

  if (allowedRoles && !allowedRoles.includes(user.role as 'doctor' | 'patient' | 'admin')) {
    return null
  }

  return <>{children}</>
}
