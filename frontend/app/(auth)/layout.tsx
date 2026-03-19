import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'SwasthyaAI — Sign In',
  description: 'Offline-first healthcare AI system',
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center shadow-md">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-6 h-6"
              >
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="text-2xl font-bold text-gray-900 tracking-tight">
              Swasthya<span className="text-teal-600">AI</span>
            </span>
          </div>
          <p className="text-sm text-gray-500">Offline-first healthcare intelligence</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {children}
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          SwasthyaAI · Designed for offline-first clinical environments
        </p>
      </div>
    </div>
  )
}
