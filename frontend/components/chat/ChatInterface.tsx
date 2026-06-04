'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { toast } from 'sonner'
import { Trash2, AlertTriangle } from 'lucide-react'
import { useChatHistory, useSendMessage, type ChatAttachment } from '@/hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { TypingIndicator } from './TypingIndicator'
import { WelcomeMessage } from './WelcomeMessage'
import { SuggestedPrompts } from './SuggestedPrompts'
import { ChatInput, type SelectedFile } from './ChatInput'
import type { User } from '@/types'

interface ChatInterfaceProps {
  user: User
  patientId?: string                       // doctor: ?patientId= in URL
  patientContext?: Record<string, unknown> // doctor: patient summary forwarded to API
  /** When set (from /documents "Analyze with AI"), auto-sends this image once. */
  analyzeImage?: { base64: string; mimeType: string; fileName: string } | null
  onAnalyzeConsumed?: () => void
}

function getUserInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/** Read a File into a base64 string (no data: prefix). */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const r = reader.result as string
      resolve(r.includes(',') ? r.split(',')[1] : r)
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

export function ChatInterface({
  user,
  patientId,
  patientContext,
  analyzeImage,
  onAnalyzeConsumed,
}: ChatInterfaceProps) {
  const { messages, addMessage, clearMessages } = useChatHistory(user.id)
  const sendMutation = useSendMessage(addMessage)
  const bottomRef = useRef<HTMLDivElement>(null)

  const [pendingPrompt, setPendingPrompt] = useState('')
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  const isLoading = sendMutation.isPending
  const showSuggestions = messages.length === 0 && !isLoading

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const sendImage = useCallback(
    (params: {
      text: string
      base64: string
      mimeType: string
      preview: string
      fileName: string
    }) => {
      const modality = /x.?ray|chest/i.test(params.fileName) ? 'xray' : 'other'
      const attachment: ChatAttachment = {
        preview: params.preview,
        fileName: params.fileName,
        mimeType: params.mimeType,
      }
      sendMutation.mutate(
        {
          query: params.text,
          patientId,
          attachment,
          context: {
            ...(patientContext ?? {}),
            image_data: params.base64,
            modality,
            analysis_type: 'finding_detection',
          },
        },
        { onError: () => toast.error('Failed to analyze the image. Check your connection.') }
      )
    },
    [sendMutation, patientId, patientContext]
  )

  // Auto-send a document image routed from /documents "Analyze with AI".
  const analyzedRef = useRef(false)
  useEffect(() => {
    if (!analyzeImage || analyzedRef.current) return
    analyzedRef.current = true
    sendImage({
      text: `Please analyze this medical image: ${analyzeImage.fileName}`,
      base64: analyzeImage.base64,
      mimeType: analyzeImage.mimeType,
      preview: `data:${analyzeImage.mimeType};base64,${analyzeImage.base64}`,
      fileName: analyzeImage.fileName,
    })
    onAnalyzeConsumed?.()
  }, [analyzeImage, sendImage, onAnalyzeConsumed])

  async function handleSend(text: string, file?: SelectedFile | null) {
    if (file && file.file.type.startsWith('image/')) {
      try {
        const base64 = await fileToBase64(file.file)
        sendImage({
          text: text || `Please analyze this medical image: ${file.file.name}`,
          base64,
          mimeType: file.file.type,
          preview: file.preview ?? `data:${file.file.type};base64,${base64}`,
          fileName: file.file.name,
        })
      } catch {
        toast.error('Could not read the attached image.')
      }
      return
    }

    // Text-only message (PDF attachments are not analyzed in-chat).
    if (file && !file.file.type.startsWith('image/')) {
      toast.message('Only images can be analyzed in chat. Upload PDFs from Documents.')
    }
    sendMutation.mutate(
      { query: text, patientId, context: patientContext },
      { onError: () => toast.error('Failed to get a response. Check your connection.') }
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

  // Surface a stub-mode banner if the most recent assistant reply was a demo.
  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')
  const showStubBanner = !!lastAssistant?.isStub

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

      {/* Stub-mode banner */}
      {showStubBanner && (
        <div className="flex items-start gap-2 px-6 py-2 bg-amber-50 border-b border-amber-200 text-amber-800">
          <AlertTriangle size={15} className="mt-0.5 flex-shrink-0" />
          <p className="text-xs leading-relaxed">
            <span className="font-semibold">AI model not loaded — demo output.</span>{' '}
            Responses are illustrative placeholders, not real medical analysis. Do not rely on
            them for clinical decisions.
          </p>
        </div>
      )}

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
