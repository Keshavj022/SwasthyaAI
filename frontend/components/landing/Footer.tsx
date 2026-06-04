import Link from 'next/link'
import { Activity } from 'lucide-react'

const LINKS = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Safety Guidelines', href: '/safety' },
  { label: 'Documentation', href: '/docs' },
]

export default function Footer() {
  return (
    <footer
      className="text-teal-50"
      style={{ background: 'linear-gradient(160deg, #0F4C5C 0%, #14586a 100%)' }}
    >
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3 md:items-center">
          {/* Left: brand */}
          <div className="text-center md:text-left">
            <Link href="/" className="inline-flex items-center gap-2 text-white">
              <Activity className="h-5 w-5" style={{ color: '#1DB8A0' }} strokeWidth={2.5} aria-hidden="true" />
              <span className="text-lg font-bold tracking-tight">SwasthyaAI</span>
            </Link>
            <p className="mt-1.5 text-sm text-teal-100/80">
              An offline-first hospital AI system
            </p>
          </div>

          {/* Center: links */}
          <nav aria-label="Footer" className="flex flex-wrap justify-center gap-x-6 gap-y-2">
            {LINKS.map(({ label, href }) => (
              <Link
                key={label}
                href={href}
                className="text-sm text-teal-100/90 transition-colors hover:text-white"
              >
                {label}
              </Link>
            ))}
          </nav>

          {/* Right: attribution */}
          <p className="text-center text-sm text-teal-100/80 md:text-right">
            Built for Google Health AI Developer Foundations
          </p>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto max-w-6xl px-6 py-4 text-center text-xs text-teal-100/70">
          © 2026 SwasthyaAI
        </div>
      </div>
    </footer>
  )
}
