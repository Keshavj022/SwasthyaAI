'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'

// ─── Types ───────────────────────────────────────────────────────────────────

type Role = 'doctors' | 'patients'

// ─── Static data ─────────────────────────────────────────────────────────────

const STATS = [
  { value: '10', label: 'AI Agents', sub: 'Specialized for every clinical need' },
  { value: '100%', label: 'Offline-First', sub: 'Works without internet connection' },
  { value: 'Local', label: 'Privacy-Preserving', sub: 'All data stays on your device' },
  { value: 'Open', label: 'Source Models', sub: 'Powered by open medical AI' },
]

const FEATURES = [
  {
    emoji: '🩺',
    title: 'Symptom Assessment',
    description: 'Check symptoms and receive AI-powered triage recommendations instantly.',
  },
  {
    emoji: '💊',
    title: 'Drug Info & Interactions',
    description: 'Safe medication guidance with instant drug interaction checking.',
  },
  {
    emoji: '🔬',
    title: 'Diagnostic Support',
    description: 'Differential diagnosis assistance powered by local medical AI.',
  },
  {
    emoji: '📅',
    title: 'Appointment Scheduling',
    description: 'Book and manage appointments with healthcare providers.',
  },
  {
    emoji: '🧬',
    title: 'Lab Results Interpreter',
    description: 'Understand your lab reports in clear, plain language.',
  },
  {
    emoji: '🖼',
    title: 'Image Analysis',
    description: 'X-ray and scan review support with AI-powered interpretation.',
  },
]

const STEPS: Record<Role, { step: string; title: string; description: string }[]> = {
  doctors: [
    { step: '01', title: 'Log in with credentials', description: 'Secure access using your medical provider credentials' },
    { step: '02', title: 'Access AI diagnostic assistant', description: 'Get instant differential diagnosis and clinical decision support' },
    { step: '03', title: 'Check drug interactions', description: 'Verify medication safety instantly before prescribing' },
    { step: '04', title: 'View patient records & documents', description: 'Access complete patient history, labs, and uploaded documents' },
    { step: '05', title: 'Manage your schedule', description: 'Organise appointments and streamline your clinical workflow' },
  ],
  patients: [
    { step: '01', title: 'Register your health profile', description: 'Create your personal health record securely on the device' },
    { step: '02', title: 'Describe your symptoms', description: 'Tell SwasthyaAI how you are feeling in your own words' },
    { step: '03', title: 'Get plain-language guidance', description: 'Receive clear, understandable health information and next steps' },
    { step: '04', title: 'Book appointments', description: 'Connect with nearby healthcare providers easily' },
    { step: '05', title: 'Track health goals daily', description: 'Monitor your progress and wellbeing over time' },
  ],
}

const SAFETY_POINTS = [
  {
    icon: '🔒',
    title: 'Local Data Storage',
    description: 'All patient data is stored locally on-device using SQLite — it never leaves your hardware.',
  },
  {
    icon: '⚕️',
    title: 'AI Safety Disclaimers',
    description: 'Every AI-generated output includes mandatory clinical safety disclaimers.',
  },
  {
    icon: '🚨',
    title: 'Emergency Detection',
    description: 'Automatic recognition of emergency symptoms with immediate escalation protocols.',
  },
  {
    icon: '📋',
    title: 'Complete Audit Trail',
    description: 'Full audit log of every AI interaction for clinical accountability and review.',
  },
]

const TECH_BADGES = ['Next.js 15', 'FastAPI', 'SQLite', 'Google Medical AI', 'MedGemma', 'PyTorch', 'Transformers']

// ─── Icons ───────────────────────────────────────────────────────────────────

function HeartbeatIcon({ size = 28, color = 'white' }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M2 12h4l3-7 4 14 3-8 2 4h4"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function WaveDivider() {
  return (
    <div style={{ lineHeight: 0, overflow: 'hidden' }} aria-hidden="true">
      <svg
        viewBox="0 0 1440 80"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        style={{ display: 'block', width: '100%', height: 80 }}
      >
        <path
          d="M0,32 C180,72 360,8 540,40 C720,72 900,8 1080,40 C1260,72 1380,20 1440,36 L1440,80 L0,80 Z"
          fill="white"
        />
      </svg>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function LandingPage() {
  const { isAuthenticated, user } = useAuth()
  const router = useRouter()
  const [activeRole, setActiveRole] = useState<Role>('doctors')

  useEffect(() => {
    if (isAuthenticated && user) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, user, router])

  const scrollToFeatures = useCallback(() => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  return (
    <>
      <style>{`
        :root {
          --land-teal: #0F4C5C;
          --land-teal-mid: #1A6B7C;
          --land-accent: #1DB8A0;
          --land-text: #1A1A2E;
          --land-muted: #4A6070;
          --land-bg-gray: #F4F7F9;
        }

        @keyframes land-fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes land-fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes land-scaleIn {
          from { opacity: 0; transform: scale(0.94); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes land-pulse-ring {
          0% { transform: scale(1); opacity: 0.6; }
          100% { transform: scale(1.8); opacity: 0; }
        }

        @media (prefers-reduced-motion: reduce) {
          .land-anim { animation: none !important; opacity: 1 !important; transform: none !important; }
        }

        .land-hero-section {
          background: linear-gradient(145deg, #0A3443 0%, #0F4C5C 40%, #1A6B7C 75%, #0D4A5A 100%);
          position: relative;
          overflow: hidden;
        }
        .land-hero-dots {
          position: absolute;
          inset: 0;
          background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
          background-size: 36px 36px;
          pointer-events: none;
        }
        .land-hero-glow {
          position: absolute;
          width: 600px;
          height: 600px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(29,184,160,0.15) 0%, transparent 70%);
          left: -100px;
          bottom: -100px;
          pointer-events: none;
        }
        .land-hero-glow-2 {
          position: absolute;
          width: 400px;
          height: 400px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
          right: -50px;
          top: 80px;
          pointer-events: none;
        }

        .land-badge {
          animation: land-fadeIn 0.5s ease both;
        }
        .land-h1 { animation: land-fadeUp 0.65s ease both; animation-delay: 0.1s; }
        .land-sub1 { animation: land-fadeUp 0.65s ease both; animation-delay: 0.22s; }
        .land-sub2 { animation: land-fadeUp 0.65s ease both; animation-delay: 0.32s; }
        .land-ctas { animation: land-fadeUp 0.65s ease both; animation-delay: 0.42s; }

        .land-cta-primary {
          background: white;
          color: var(--land-teal);
          font-weight: 700;
          padding: 14px 34px;
          border-radius: 100px;
          font-size: 0.975rem;
          transition: all 0.2s ease;
          display: inline-block;
          border: none;
          cursor: pointer;
          text-decoration: none;
          letter-spacing: -0.01em;
          line-height: 1;
        }
        .land-cta-primary:hover {
          background: rgba(255,255,255,0.92);
          transform: translateY(-2px);
          box-shadow: 0 10px 28px rgba(0,0,0,0.22);
          color: var(--land-teal);
          text-decoration: none;
        }

        .land-cta-ghost {
          background: transparent;
          color: white;
          font-weight: 600;
          padding: 14px 34px;
          border-radius: 100px;
          font-size: 0.975rem;
          transition: all 0.2s ease;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1.5px solid rgba(255,255,255,0.35);
          cursor: pointer;
          text-decoration: none;
          letter-spacing: -0.01em;
          line-height: 1;
        }
        .land-cta-ghost:hover {
          background: rgba(255,255,255,0.1);
          border-color: rgba(255,255,255,0.65);
          transform: translateY(-2px);
          color: white;
        }

        .land-cta-sm {
          padding: 10px 22px !important;
          font-size: 0.875rem !important;
        }

        .land-feature-card {
          background: white;
          border-radius: 18px;
          border: 1px solid #E2EDF0;
          padding: 28px 24px;
          transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        }
        .land-feature-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 18px 44px rgba(15,76,92,0.11);
          border-color: rgba(29,184,160,0.5);
        }

        .land-tab-pill {
          transition: all 0.2s ease;
          font-weight: 600;
          border-radius: 100px;
          padding: 9px 26px;
          font-size: 0.9rem;
          cursor: pointer;
          border: none;
          background: transparent;
          color: var(--land-teal);
        }
        .land-tab-pill.active {
          background: var(--land-teal);
          color: white;
        }
        .land-tab-pill:not(.active):hover {
          background: rgba(15,76,92,0.07);
        }

        .land-step-num {
          flex-shrink: 0;
          width: 48px;
          height: 48px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 0.82rem;
          letter-spacing: -0.01em;
        }
        .land-step-num.first {
          background: var(--land-teal);
          color: white;
        }
        .land-step-num.rest {
          background: white;
          border: 1.5px solid #DCE9ED;
          color: var(--land-teal);
        }

        .land-safety-card {
          background: white;
          border-radius: 16px;
          padding: 24px;
          border: 1px solid #E5EDF1;
          animation: land-scaleIn 0.5s ease both;
        }
        .land-safety-card:hover {
          box-shadow: 0 8px 24px rgba(15,76,92,0.08);
        }

        .land-tech-badge {
          display: inline-block;
          padding: 8px 18px;
          border-radius: 100px;
          font-size: 0.83rem;
          font-weight: 600;
          background: rgba(15,76,92,0.07);
          color: var(--land-teal);
          border: 1px solid rgba(15,76,92,0.14);
          transition: all 0.18s ease;
          cursor: default;
        }
        .land-tech-badge:hover {
          background: var(--land-teal);
          color: white;
          border-color: var(--land-teal);
        }

        .land-footer-link {
          color: rgba(255,255,255,0.6);
          font-size: 0.9rem;
          text-decoration: none;
          transition: color 0.15s;
          display: block;
        }
        .land-footer-link:hover {
          color: #1DB8A0;
        }

        .land-section-label {
          color: var(--land-accent);
          font-weight: 700;
          font-size: 0.78rem;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          margin-bottom: 12px;
          display: block;
        }
        .land-section-title {
          font-size: clamp(1.85rem, 4vw, 2.75rem);
          font-weight: 900;
          letter-spacing: -0.04em;
          color: var(--land-text);
          line-height: 1.12;
          margin: 0;
        }

        html { scroll-behavior: smooth; }
      `}</style>

      <div
        style={{
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', 'Helvetica Neue', system-ui, sans-serif",
          color: 'var(--land-text)',
          lineHeight: 1.6,
        }}
      >
        {/* ── 1. HERO ─────────────────────────────────────────────────────── */}
        <section className="land-hero-section" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <div className="land-hero-dots" />
          <div className="land-hero-glow" />
          <div className="land-hero-glow-2" />

          {/* Nav */}
          <nav
            style={{
              padding: '20px 32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              position: 'relative',
              zIndex: 10,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <HeartbeatIcon size={22} color="#1DB8A0" />
              <span
                style={{
                  color: 'white',
                  fontWeight: 800,
                  fontSize: '1.2rem',
                  letterSpacing: '-0.04em',
                }}
              >
                SwasthyaAI
              </span>
            </div>
            <Link href="/login" className="land-cta-primary land-cta-sm">
              Login
            </Link>
          </nav>

          {/* Hero content */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 'clamp(40px, 8vw, 80px) 24px 20px',
              textAlign: 'center',
              position: 'relative',
              zIndex: 10,
            }}
          >
            {/* Eyebrow badge */}
            <div
              className="land-badge land-anim"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(29,184,160,0.14)',
                border: '1px solid rgba(29,184,160,0.38)',
                borderRadius: 100,
                padding: '7px 18px',
                marginBottom: 28,
              }}
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#1DB8A0',
                  display: 'inline-block',
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  color: '#1DB8A0',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  letterSpacing: '0.07em',
                  textTransform: 'uppercase',
                }}
              >
                Offline-first · Privacy-preserving · Open models
              </span>
            </div>

            {/* Headline */}
            <h1
              className="land-h1 land-anim"
              style={{
                fontSize: 'clamp(2.4rem, 6.5vw, 4.4rem)',
                fontWeight: 900,
                color: 'white',
                lineHeight: 1.08,
                letterSpacing: '-0.045em',
                maxWidth: 860,
                marginBottom: 22,
              }}
            >
              Hospital AI that works{' '}
              <span style={{ color: '#1DB8A0' }}>anywhere</span>{' '}
              care is delivered
            </h1>

            {/* Sub-tagline */}
            <p
              className="land-sub1 land-anim"
              style={{
                fontSize: 'clamp(1rem, 2.5vw, 1.2rem)',
                color: 'rgba(255,255,255,0.75)',
                maxWidth: 580,
                marginBottom: 10,
                fontWeight: 400,
                lineHeight: 1.65,
              }}
            >
              Clinical decision support, symptom assessment, and diagnostic aid — all running locally, no internet required.
            </p>

            <p
              className="land-sub2 land-anim"
              style={{
                fontSize: '0.92rem',
                color: 'rgba(255,255,255,0.45)',
                marginBottom: 48,
                fontWeight: 400,
              }}
            >
              Built for doctors and patients in resource-limited settings
            </p>

            {/* CTAs */}
            <div
              className="land-ctas land-anim"
              style={{ display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center' }}
            >
              <Link href="/login" className="land-cta-primary">
                Login to SwasthyaAI
              </Link>
              <button className="land-cta-ghost" onClick={scrollToFeatures}>
                Learn More ↓
              </button>
            </div>
          </div>

          {/* Wave */}
          <div style={{ position: 'relative', zIndex: 10 }}>
            <WaveDivider />
          </div>
        </section>

        {/* ── 2. STATS BAR ─────────────────────────────────────────────────── */}
        <section style={{ background: 'white', padding: 'clamp(40px, 6vw, 64px) 24px' }}>
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
                gap: '28px 40px',
              }}
            >
              {STATS.map((stat, i) => (
                <div
                  key={i}
                  className="land-anim"
                  style={{ textAlign: 'center', animationDelay: `${i * 0.08}s` }}
                >
                  <div
                    style={{
                      fontSize: 'clamp(1.9rem, 4vw, 2.8rem)',
                      fontWeight: 900,
                      color: 'var(--land-teal)',
                      letterSpacing: '-0.045em',
                      lineHeight: 1,
                    }}
                  >
                    {stat.value}
                  </div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: 'var(--land-text)',
                      marginTop: 5,
                      fontSize: '1rem',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {stat.label}
                  </div>
                  <div style={{ color: 'var(--land-muted)', fontSize: '0.84rem', marginTop: 3 }}>
                    {stat.sub}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div
          style={{
            height: 1,
            background: 'linear-gradient(to right, transparent, #E0ECF0, transparent)',
            maxWidth: 1100,
            margin: '0 auto',
          }}
        />

        {/* ── 3. FEATURES GRID ─────────────────────────────────────────────── */}
        <section
          id="features"
          style={{ background: 'white', padding: 'clamp(64px, 9vw, 108px) 24px' }}
        >
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 56 }}>
              <span className="land-section-label">What SwasthyaAI does</span>
              <h2 className="land-section-title">A complete AI system for healthcare</h2>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
                gap: 22,
              }}
            >
              {FEATURES.map((f, i) => (
                <div
                  key={i}
                  className="land-feature-card land-anim"
                  style={{ animationDelay: `${i * 0.07}s` }}
                >
                  <div
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: 14,
                      background: 'linear-gradient(135deg, #E6F5F3, #CCF0EA)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.4rem',
                      marginBottom: 18,
                    }}
                  >
                    {f.emoji}
                  </div>
                  <h3
                    style={{
                      fontWeight: 800,
                      fontSize: '1.05rem',
                      color: 'var(--land-text)',
                      marginBottom: 8,
                      letterSpacing: '-0.025em',
                    }}
                  >
                    {f.title}
                  </h3>
                  <p style={{ color: 'var(--land-muted)', fontSize: '0.9rem', lineHeight: 1.65, margin: 0 }}>
                    {f.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── 4. HOW IT WORKS ──────────────────────────────────────────────── */}
        <section style={{ background: 'var(--land-bg-gray)', padding: 'clamp(64px, 9vw, 108px) 24px' }}>
          <div style={{ maxWidth: 820, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 44 }}>
              <span className="land-section-label">How it works</span>
              <h2 className="land-section-title" style={{ marginBottom: 32 }}>
                For doctors and patients
              </h2>

              {/* Tab toggle */}
              <div
                style={{
                  display: 'inline-flex',
                  background: 'white',
                  borderRadius: 100,
                  padding: 5,
                  border: '1px solid #DDE8EC',
                }}
              >
                <button
                  className={`land-tab-pill${activeRole === 'doctors' ? ' active' : ''}`}
                  onClick={() => setActiveRole('doctors')}
                >
                  For Doctors
                </button>
                <button
                  className={`land-tab-pill${activeRole === 'patients' ? ' active' : ''}`}
                  onClick={() => setActiveRole('patients')}
                >
                  For Patients
                </button>
              </div>
            </div>

            {/* Steps */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {STEPS[activeRole].map((s, i) => (
                <div
                  key={`${activeRole}-${i}`}
                  className="land-anim"
                  style={{
                    display: 'flex',
                    gap: 20,
                    alignItems: 'flex-start',
                    animationDelay: `${i * 0.06}s`,
                    padding: '18px 0',
                    borderBottom:
                      i < STEPS[activeRole].length - 1
                        ? '1px solid rgba(15,76,92,0.08)'
                        : 'none',
                  }}
                >
                  <div className={`land-step-num ${i === 0 ? 'first' : 'rest'}`}>{s.step}</div>
                  <div style={{ paddingTop: 8 }}>
                    <div
                      style={{
                        fontWeight: 700,
                        fontSize: '1rem',
                        color: 'var(--land-text)',
                        marginBottom: 4,
                        letterSpacing: '-0.015em',
                      }}
                    >
                      {s.title}
                    </div>
                    <div style={{ color: 'var(--land-muted)', fontSize: '0.9rem' }}>
                      {s.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <Link href="/login" className="land-cta-primary" style={{ background: 'var(--land-teal)', color: 'white' }}>
                Get Started →
              </Link>
            </div>
          </div>
        </section>

        {/* ── 5. SAFETY & PRIVACY ──────────────────────────────────────────── */}
        <section style={{ background: 'white', padding: 'clamp(64px, 9vw, 108px) 24px' }}>
          <div style={{ maxWidth: 960, margin: '0 auto', textAlign: 'center' }}>
            {/* Shield */}
            <div style={{ marginBottom: 20 }}>
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 22,
                  background: 'linear-gradient(135deg, #E6F5F3, #C8EDE8)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem',
                }}
              >
                🛡️
              </div>
            </div>

            <span className="land-section-label">Safety first</span>
            <h2 className="land-section-title" style={{ marginBottom: 48 }}>
              Built with safety at its core
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: 20,
                marginBottom: 44,
                textAlign: 'left',
              }}
            >
              {SAFETY_POINTS.map((p, i) => (
                <div
                  key={i}
                  className="land-safety-card"
                  style={{ animationDelay: `${i * 0.09}s` }}
                >
                  <div style={{ fontSize: '1.5rem', marginBottom: 12 }}>{p.icon}</div>
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: '0.975rem',
                      color: 'var(--land-text)',
                      marginBottom: 6,
                      letterSpacing: '-0.015em',
                    }}
                  >
                    {p.title}
                  </div>
                  <div style={{ color: 'var(--land-muted)', fontSize: '0.875rem', lineHeight: 1.65 }}>
                    {p.description}
                  </div>
                </div>
              ))}
            </div>

            {/* Disclaimer banner */}
            <div
              style={{
                background: 'linear-gradient(135deg, #FFFAF3, #FFF5E4)',
                border: '1px solid #FDDBA0',
                borderRadius: 16,
                padding: '20px 32px',
                maxWidth: 720,
                margin: '0 auto',
              }}
            >
              <p
                style={{
                  margin: 0,
                  color: '#6B3C00',
                  fontSize: '0.9rem',
                  lineHeight: 1.75,
                  fontWeight: 500,
                }}
              >
                <strong>⚠️ Important:</strong> SwasthyaAI is a clinical decision{' '}
                <strong>SUPPORT</strong> tool. It does not replace a qualified healthcare
                professional. Always consult a licensed clinician for medical decisions.
              </p>
            </div>
          </div>
        </section>

        {/* ── 6. TECH STACK ────────────────────────────────────────────────── */}
        <section style={{ background: 'var(--land-bg-gray)', padding: 'clamp(48px, 6vw, 76px) 24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
            <p
              style={{
                color: 'var(--land-muted)',
                fontWeight: 600,
                fontSize: '0.78rem',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginBottom: 24,
              }}
            >
              Powered by open technology
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', marginBottom: 20 }}>
              {TECH_BADGES.map((badge, i) => (
                <span key={i} className="land-tech-badge">
                  {badge}
                </span>
              ))}
            </div>
            <p style={{ color: 'var(--land-muted)', fontSize: '0.875rem', margin: 0 }}>
              Fully offline-capable — no cloud required for core features
            </p>
          </div>
        </section>

        {/* ── 7. FOOTER ────────────────────────────────────────────────────── */}
        <footer
          style={{
            background: 'var(--land-teal)',
            color: 'rgba(255,255,255,0.8)',
            padding: 'clamp(44px, 6vw, 72px) 24px 24px',
          }}
        >
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '40px 48px',
                marginBottom: 40,
              }}
            >
              {/* Brand */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 14 }}>
                  <HeartbeatIcon size={20} color="#1DB8A0" />
                  <span
                    style={{
                      color: 'white',
                      fontWeight: 800,
                      fontSize: '1.15rem',
                      letterSpacing: '-0.04em',
                    }}
                  >
                    SwasthyaAI
                  </span>
                </div>
                <p
                  style={{
                    fontSize: '0.875rem',
                    color: 'rgba(255,255,255,0.5)',
                    margin: 0,
                    lineHeight: 1.75,
                    maxWidth: 260,
                  }}
                >
                  An offline-first hospital AI system delivering clinical decision support anywhere care is needed.
                </p>
              </div>

              {/* Links */}
              <div>
                <p
                  style={{
                    color: 'rgba(255,255,255,0.35)',
                    fontWeight: 600,
                    fontSize: '0.74rem',
                    letterSpacing: '0.09em',
                    textTransform: 'uppercase',
                    marginBottom: 16,
                  }}
                >
                  Links
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <a href="#" className="land-footer-link">Privacy Policy</a>
                  <a href="#" className="land-footer-link">Safety Guidelines</a>
                  <a href="#" className="land-footer-link">Documentation</a>
                </div>
              </div>

              {/* Attribution */}
              <div>
                <p
                  style={{
                    color: 'rgba(255,255,255,0.35)',
                    fontWeight: 600,
                    fontSize: '0.74rem',
                    letterSpacing: '0.09em',
                    textTransform: 'uppercase',
                    marginBottom: 16,
                  }}
                >
                  Built for
                </p>
                <p
                  style={{
                    color: 'rgba(255,255,255,0.62)',
                    fontSize: '0.9rem',
                    lineHeight: 1.7,
                    margin: '0 0 20px',
                  }}
                >
                  Google Health AI Developer Foundations
                </p>
                <Link href="/login" className="land-cta-primary land-cta-sm">
                  Get Started →
                </Link>
              </div>
            </div>

            {/* Bottom bar */}
            <div
              style={{
                borderTop: '1px solid rgba(255,255,255,0.1)',
                paddingTop: 20,
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 10,
              }}
            >
              <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.8rem', margin: 0 }}>
                © 2026 SwasthyaAI. All rights reserved.
              </p>
              <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.8rem', margin: 0 }}>
                Powered by MedGemma · MedSigLIP · MedASR
              </p>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}
