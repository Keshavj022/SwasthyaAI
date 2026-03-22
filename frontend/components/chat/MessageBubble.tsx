'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Check } from 'lucide-react'
import { toast } from 'sonner'
import type { Message } from '@/types'

// ---------------------------------------------------------------------------
// Agent badge config
// ---------------------------------------------------------------------------

const AGENT_CONFIG: Record<string, { label: string; colorClass: string }> = {
  communication:      { label: 'Communication', colorClass: 'bg-teal-100 text-teal-800' },
  diagnostic_support: { label: 'Diagnostic',    colorClass: 'bg-purple-100 text-purple-800' },
  drug_info:          { label: 'Drug Info',      colorClass: 'bg-blue-100 text-blue-800' },
  triage:             { label: 'Triage',         colorClass: 'bg-red-100 text-red-800' },
  image_analysis:     { label: 'Image Analysis', colorClass: 'bg-orange-100 text-orange-800' },
  appointment:        { label: 'Appointments',   colorClass: 'bg-green-100 text-green-800' },
  health_support:     { label: 'Health Support', colorClass: 'bg-cyan-100 text-cyan-800' },
  nearby_doctors:     { label: 'Find Doctors',   colorClass: 'bg-indigo-100 text-indigo-800' },
  orchestrator:       { label: 'General',        colorClass: 'bg-gray-100 text-gray-700' },
}

function getAgentConfig(agentType?: string) {
  if (!agentType) return AGENT_CONFIG.orchestrator
  return AGENT_CONFIG[agentType] ?? { label: agentType, colorClass: 'bg-gray-100 text-gray-700' }
}

// ---------------------------------------------------------------------------
// Confidence bar
// ---------------------------------------------------------------------------

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, Math.round(score * 100)))
  const colorClass =
    pct >= 80 ? 'bg-green-500' :
    pct >= 60 ? 'bg-amber-400' :
                'bg-red-400'

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="text-xs text-gray-400">{pct}% confidence</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Format timestamp
// ---------------------------------------------------------------------------

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

// ---------------------------------------------------------------------------
// MessageBubble
// ---------------------------------------------------------------------------

interface MessageBubbleProps {
  message: Message
  userInitials: string
}

export function MessageBubble({ message, userInitials }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)

  const isUser = message.role === 'user'

  // ---------------------------------------------------------------------------
  // User bubble (right-aligned)
  // ---------------------------------------------------------------------------

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-2 px-4 py-1">
        <div className="max-w-[70%]">
          <div className="bg-teal-600 text-white px-4 py-2.5 rounded-2xl rounded-br-sm shadow-sm">
            {message.attachmentUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={message.attachmentUrl}
                alt="Attached image"
                className="max-w-[200px] rounded-lg mb-2 border border-teal-200"
              />
            )}
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </div>
          <p className="text-xs text-gray-400 mt-1 text-right">{formatTime(message.timestamp)}</p>
        </div>
        {/* Initials avatar */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-teal-700 flex items-center justify-center text-white text-xs font-bold shadow-sm">
          {userInitials}
        </div>
      </div>
    )
  }

  // ---------------------------------------------------------------------------
  // Assistant bubble (left-aligned)
  // ---------------------------------------------------------------------------

  const agentConf = getAgentConfig(message.agentType)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard not available (non-HTTPS or permission denied)
      toast.error('Could not copy to clipboard')
    }
  }

  return (
    <div className="flex items-start gap-3 px-4 py-1">
      {/* AI avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-bold shadow-sm mt-1">
        AI
      </div>

      {/* Card */}
      <div className="max-w-[80%] bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm overflow-hidden">
        {/* Card header: agent badge + copy */}
        <div className="flex items-center justify-between px-4 pt-3 pb-1">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${agentConf.colorClass}`}
          >
            {agentConf.label}
          </span>
          <button
            onClick={handleCopy}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded"
            title="Copy response"
          >
            {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
          </button>
        </div>

        {/* Message body */}
        <div className="px-4 py-2">
          <div className="prose prose-sm max-w-none text-gray-800 text-sm
                          [&>p]:mb-2 [&>ul]:mb-2 [&>ol]:mb-2 [&>h1]:text-base [&>h2]:text-sm [&>h3]:text-sm
                          [&>ul]:pl-4 [&>ol]:pl-4 [&>li]:mb-0.5 [&>code]:bg-gray-100 [&>code]:px-1 [&>code]:rounded">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Confidence bar */}
          {message.confidence !== undefined && (
            <ConfidenceBar score={message.confidence} />
          )}

          {/* Reasoning toggle */}
          {message.reasoning && (
            <div className="mt-2 border-t border-gray-100 pt-2">
              <button
                onClick={() => setShowReasoning((v) => !v)}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
              >
                {showReasoning ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {showReasoning ? 'Hide reasoning' : 'Show reasoning'}
              </button>
              {showReasoning && (
                <p className="text-xs text-gray-500 mt-1 italic bg-gray-50 rounded p-2 whitespace-pre-wrap">
                  {message.reasoning}
                </p>
              )}
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-xs text-gray-400 italic mt-2 border-t border-gray-100 pt-2">
            {message.disclaimer ?? 'This information is for clinical decision support only. Always consult a qualified healthcare professional.'}
          </p>
        </div>

        {/* Footer: timestamp + thumbs */}
        <div className="flex items-center justify-between px-4 pb-3 pt-1">
          <p className="text-xs text-gray-400">{formatTime(message.timestamp)}</p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
              className={`p-1 rounded transition-colors ${
                feedback === 'up' ? 'text-green-500' : 'text-gray-300 hover:text-gray-500'
              }`}
              title="Helpful"
            >
              <ThumbsUp size={12} />
            </button>
            <button
              onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
              className={`p-1 rounded transition-colors ${
                feedback === 'down' ? 'text-red-400' : 'text-gray-300 hover:text-gray-500'
              }`}
              title="Not helpful"
            >
              <ThumbsDown size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
