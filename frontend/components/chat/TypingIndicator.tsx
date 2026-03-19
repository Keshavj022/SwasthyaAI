'use client'

export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-2">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-bold">
        AI
      </div>

      {/* Bubble */}
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-500 mr-2">SwasthyaAI is thinking</span>
          <span
            className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  )
}
