'use client'

import Link from 'next/link'
import { Activity, ArrowRight, ChevronDown, LayoutDashboard } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'

const DASHBOARD: Record<string, string> = {
  patient: '/dashboard/patient',
  doctor: '/dashboard/doctor',
  admin: '/dashboard/admin',
}

export default function Hero() {
  const { isAuthenticated, user } = useAuth()
  const dashboardHref = (user?.role && DASHBOARD[user.role]) || '/dashboard/patient'

  return (
    <section
      className="relative isolate overflow-hidden"
      style={{ background: 'linear-gradient(160deg, #0F4C5C 0%, #1A6B7C 100%)' }}
    >
      {/* Decorative accent glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-24 left-1/2 -z-10 h-[480px] w-[480px] -translate-x-1/2 rounded-full opacity-30 blur-3xl"
        style={{ background: 'radial-gradient(circle, #1DB8A0 0%, transparent 70%)' }}
      />

      <div className="mx-auto flex max-w-5xl flex-col items-center px-6 pb-32 pt-20 text-center sm:pt-28">
        {/* Logo wordmark */}
        <div className="mb-8 flex items-center gap-2.5 text-white">
          <span
            className="flex h-11 w-11 items-center justify-center rounded-xl"
            style={{ backgroundColor: 'rgba(29, 184, 160, 0.18)' }}
          >
            <Activity className="h-6 w-6" style={{ color: '#1DB8A0' }} strokeWidth={2.5} aria-hidden="true" />
          </span>
          <span className="text-2xl font-bold tracking-tight">SwasthyaAI</span>
        </div>

        <h1 className="landing-fade-up max-w-3xl text-balance text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
          Offline-first hospital AI — clinical decision support, anywhere care is delivered
        </h1>

        <p className="landing-fade-up landing-fade-up-delay-1 mt-6 max-w-2xl text-lg text-teal-50/90 sm:text-xl">
          Built for doctors and patients in resource-limited settings
        </p>

        <div className="landing-fade-up landing-fade-up-delay-2 mt-10 flex flex-col items-center gap-3 sm:flex-row">
          {isAuthenticated && user ? (
            <Button
              asChild
              size="lg"
              className="bg-white px-8 text-[#0F4C5C] shadow-lg hover:bg-teal-50"
            >
              <Link href={dashboardHref}>
                <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
                Go to dashboard
              </Link>
            </Button>
          ) : (
            <Button
              asChild
              size="lg"
              className="bg-white px-8 text-[#0F4C5C] shadow-lg hover:bg-teal-50"
            >
              <Link href="/register">
                Get Started
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </Button>
          )}

          {!isAuthenticated && (
            <Button
              asChild
              size="lg"
              variant="outline"
              className="border-white/40 bg-transparent px-8 text-white hover:bg-white/10 hover:text-white"
            >
              <Link href="/login">Login</Link>
            </Button>
          )}

          <a
            href="#features"
            className="inline-flex h-11 items-center justify-center gap-1.5 rounded-md px-6 text-sm font-medium text-teal-50/90 transition-colors hover:text-white"
          >
            Learn More
            <ChevronDown className="landing-bounce-soft h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </div>

      {/* Wave divider transitioning to white */}
      <div className="absolute inset-x-0 bottom-0 leading-[0]" aria-hidden="true">
        <svg
          viewBox="0 0 1440 120"
          preserveAspectRatio="none"
          className="h-[60px] w-full sm:h-[90px]"
        >
          <path
            d="M0,64 C240,120 480,120 720,80 C960,40 1200,40 1440,72 L1440,120 L0,120 Z"
            fill="#ffffff"
          />
        </svg>
      </div>
    </section>
  )
}
