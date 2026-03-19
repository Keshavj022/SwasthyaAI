'use client'

import { useAuth } from '@/hooks/useAuth'

interface WelcomeBannerProps {
  checkInDoneToday: boolean
}

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function formatDate(): string {
  return new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export default function WelcomeBanner({ checkInDoneToday }: WelcomeBannerProps) {
  const { user } = useAuth()
  const firstName = user?.name?.split(' ')[0] ?? 'there'

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {getGreeting()}, {firstName}!
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{formatDate()}</p>
        </div>
      </div>

      {!checkInDoneToday && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          <span className="text-base">⏰</span>
          <span className="font-medium">Complete your daily health check-in</span>
        </div>
      )}
    </div>
  )
}
