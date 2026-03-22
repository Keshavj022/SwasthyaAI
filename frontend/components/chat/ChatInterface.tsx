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

  const [isReadingFile, setIsReadingFile] = useState(false)

  const isLoading = sendMutation.isPending
  const showSuggestions = messages.length === 0 && !isLoading

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Pick up pending image analysis from DocumentPreviewPanel's "Analyze with AI" button
  useEffect(() => {
    if (typeof window === 'undefined') return
    const raw = sessionStorage.getItem('pendingImageAnalysis')
    if (!raw) return
    try {
      const { base64, mimeType, fileName, query } = JSON.parse(raw) as {
        base64: string
        mimeType: string
        fileName: string
        query: string
      }
      sessionStorage.removeItem('pendingImageAnalysis')
      const dataUrl = `data:${mimeType};base64,${base64}`
      sendMutation.mutate(
        {
          query,
          patientId,
          context: {
            image_data: base64,
            modality: 'other',
            analysis_type: 'finding_detection',
          },
          attachmentUrl: dataUrl,
        },
        {
          onError: () => toast.error('Failed to analyze image. Please try again.'),
        }
      )
    } catch {
      sessionStorage.removeItem('pendingImageAnalysis')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run on mount

  async function handleSend(text: string, file?: File) {
    if (file && file.type.startsWith('image/')) {
      setIsReadingFile(true)
      try {
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => {
            const r = reader.result as string
            resolve(r.split(',')[1] ?? r)
          }
          reader.onerror = () => reject(new Error('Failed to read file'))
          reader.readAsDataURL(file)
        })
        const dataUrl = `data:${file.type};base64,${base64}`
        sendMutation.mutate(
          {
            query: text,
            patientId,
            context: {
              image_data: base64,
              modality: 'other',
              analysis_type: 'finding_detection',
            },
            attachmentUrl: dataUrl,
          },
          {
            onError: () => toast.error('Failed to get a response. Check your connection.'),
          }
        )
      } catch {
        toast.error('Failed to read image file. Please try again.')
      } finally {
        setIsReadingFile(false)
      }
      return
    } else {
      sendMutation.mutate(
        { query: text, patientId },
        {
          onError: () => toast.error('Failed to get a response. Check your connection.'),
        }
      )
    }
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
        disabled={isLoading || isReadingFile}
        initialValue={pendingPrompt}
        onInitialValueConsumed={handleInitialValueConsumed}
      />
    </div>
  )
}
