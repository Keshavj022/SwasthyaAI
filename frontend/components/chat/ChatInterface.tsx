'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { toast } from 'sonner'
import { Trash2 } from 'lucide-react'
import { useChatHistory, useSendMessage } from '@/hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { TypingIndicator } from './TypingIndicator'
import { WelcomeMessage } from './WelcomeMessage'
import { SuggestedPrompts } from './SuggestedPrompts'
import { ChatInput } from './ChatInput'
import type { User } from '@/types'

interface ChatInterfaceProps {
  user: User
  patientId?: string        // passed by doctor when ?patientId= is in URL
}

function getUserInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function ChatInterface({ user, patientId }: ChatInterfaceProps) {
  const { messages, addMessage, clearMessages } = useChatHistory(user.id)
  const sendMutation = useSendMessage(addMessage)
  const bottomRef = useRef<HTMLDivElement>(null)

  // For populating input from SuggestedPrompts
  const [pendingPrompt, setPendingPrompt] = useState('')

  // Clear history confirm state
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  const isLoading = sendMutation.isPending
  const showSuggestions = messages.length === 0 && !isLoading

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function handleSend(text: string, _file?: File) {
    // _file is wired but full image analysis is Task 09
    sendMutation.mutate(
      { query: text, patientId },
      {
        onError: () => {
          toast.error('Failed to get a response. Check your connection.')
        },
      }
    )
  }

  function handleClearHistory() {
    if (!showClearConfirm) {
      setShowClearConfirm(true)
      setTimeout(() => setShowClearConfirm(false), 4000)
      return
    }
    clearMessages()
    setShowClearConfirm(false)
    toast.success('Chat history cleared')
  }

  const handleInitialValueConsumed = useCallback(() => setPendingPrompt(''), [])

  const userInitials = getUserInitials(user.name)

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200 shadow-sm">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">SwasthyaAI Assistant</h1>
          <p className="text-xs text-gray-500">AI-powered clinical decision support</p>
        </div>
        <button
          onClick={handleClearHistory}
          className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors ${
            showClearConfirm
              ? 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100 border border-gray-200'
          }`}
          title="Clear chat history"
        >
          <Trash2 size={12} />
          {showClearConfirm ? 'Confirm clear?' : 'Clear history'}
        </button>
      </div>

      {/* Message thread */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && !isLoading ? (
          <WelcomeMessage userName={user.name.split(' ')[0]} />
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} userInitials={userInitials} />
            ))}
            {isLoading && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested prompts (only when chat is empty) */}
      {showSuggestions && (
        <SuggestedPrompts
          role={user.role === 'doctor' ? 'doctor' : 'patient'}
          onSelect={(prompt) => setPendingPrompt(prompt)}
        />
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading}
        initialValue={pendingPrompt}
        onInitialValueConsumed={handleInitialValueConsumed}
      />
    </div>
  )
}
