'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Hero from '@/components/landing/Hero'
import StatsBar from '@/components/landing/StatsBar'
import FeaturesGrid from '@/components/landing/FeaturesGrid'
import HowItWorks from '@/components/landing/HowItWorks'
import SafetyPrivacy from '@/components/landing/SafetyPrivacy'
import TechStack from '@/components/landing/TechStack'
import Footer from '@/components/landing/Footer'

const DASHBOARD: Record<string, string> = {
  patient: '/dashboard/patient',
  doctor: '/dashboard/doctor',
  admin: '/dashboard/admin',
}

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuth()

  // Authenticated visitors are routed to their role dashboard. The landing
  // page still renders behind this so unauthenticated users (and the brief
  // pre-redirect frame) see content rather than a blank screen.
  useEffect(() => {
    if (isAuthenticated && user?.role) {
      router.replace(DASHBOARD[user.role] ?? '/dashboard/patient')
    }
  }, [isAuthenticated, user, router])

  return (
    <main className="min-h-screen scroll-smooth bg-white">
      {/* Scoped landing-page animations. Vanilla CSS keeps this working in the
          App Router without extra Tailwind config, and the reduced-motion guard
          disables all motion for users who request it. */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
            @keyframes landing-fade-up {
              from { opacity: 0; transform: translateY(16px); }
              to { opacity: 1; transform: translateY(0); }
            }
            @keyframes landing-bounce-soft {
              0%, 100% { transform: translateY(0); }
              50% { transform: translateY(4px); }
            }
            .landing-fade-up { opacity: 0; animation: landing-fade-up 0.6s ease-out forwards; }
            .landing-fade-up-delay-1 { animation-delay: 0.1s; }
            .landing-fade-up-delay-2 { animation-delay: 0.2s; }
            .landing-bounce-soft { animation: landing-bounce-soft 1.6s ease-in-out infinite; }
            @media (prefers-reduced-motion: reduce) {
              .landing-fade-up { opacity: 1; animation: none; }
              .landing-bounce-soft { animation: none; }
            }
          `,
        }}
      />
      <Hero />
      <StatsBar />
      <FeaturesGrid />
      <HowItWorks />
      <SafetyPrivacy />
      <TechStack />
      <Footer />
    </main>
  )
}
