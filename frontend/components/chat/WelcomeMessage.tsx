'use client'

interface WelcomeMessageProps {
  userName: string
}

export function WelcomeMessage({ userName }: WelcomeMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      {/* Logo / Icon */}
      <div className="w-16 h-16 rounded-full bg-teal-600 flex items-center justify-center mb-4 shadow-lg">
        <span className="text-white text-2xl font-bold">S</span>
      </div>

      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        Hello, {userName}. I&apos;m your AI health assistant.
      </h2>
      <p className="text-gray-600 mb-4 max-w-md">
        I can help you understand symptoms, check medications,
        book appointments, and answer health questions.
      </p>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-6 max-w-md">
        <p className="text-xs text-amber-800 italic">
          I provide clinical decision support only. Always consult a qualified healthcare
          professional for medical decisions.
        </p>
      </div>

      {/* Feature pills */}
      <div className="flex flex-wrap gap-2 justify-center">
        {['Ask health questions', 'Check medications', 'Book appointments'].map((label) => (
          <span
            key={label}
            className="px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-700 text-sm font-medium"
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
