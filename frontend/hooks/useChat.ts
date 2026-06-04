import { useState, useCallback, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { orchestratorApi } from '@/lib/api'
import type { Message, AgentResponse } from '@/types'

// ---------------------------------------------------------------------------
// Extended message
//
// The shared `Message` type is a spine file we don't own. We carry two extra,
// optional fields the chat UI needs:
//   - attachment: a preview of an image the user attached (data URL + meta)
//   - data:       the full structured agent payload (findings, diagnoses, …)
//   - isStub:     whether the responding model was in stub/demo mode
// These serialise cleanly to localStorage alongside the base Message fields.
// ---------------------------------------------------------------------------

export interface ChatAttachment {
  preview: string          // data URL (image) — shown in the bubble
  fileName: string
  mimeType: string
}

export interface ChatMessage extends Message {
  attachment?: ChatAttachment
  data?: Record<string, unknown>
  isStub?: boolean
}

// ---------------------------------------------------------------------------
// useChatHistory — message state with localStorage persistence
// ---------------------------------------------------------------------------

interface UseChatHistoryReturn {
  messages: ChatMessage[]
  addMessage: (msg: Omit<ChatMessage, 'id'>) => ChatMessage
  clearMessages: () => void
}

export function useChatHistory(userId?: string): UseChatHistoryReturn {
  const storageKey = userId ? `swasthya_chat_${userId}` : null

  const [messages, setMessages] = useState<ChatMessage[]>(() => [])

  useEffect(() => {
    if (typeof window === 'undefined' || !storageKey) return
    try {
      const stored = localStorage.getItem(storageKey)
      setMessages(stored ? (JSON.parse(stored) as ChatMessage[]) : [])
    } catch {
      setMessages([])
    }
  }, [storageKey])

  const addMessage = useCallback(
    (msg: Omit<ChatMessage, 'id'>): ChatMessage => {
      const full: ChatMessage = { ...msg, id: crypto.randomUUID() }
      setMessages((prev) => {
        const next = [...prev, full]
        const stored = next.slice(-200) // keep last 200 messages
        if (typeof window !== 'undefined' && storageKey) {
          localStorage.setItem(storageKey, JSON.stringify(stored))
        }
        return stored
      })
      return full
    },
    [storageKey]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    if (typeof window !== 'undefined' && storageKey) {
      localStorage.removeItem(storageKey)
    }
  }, [storageKey])

  return { messages, addMessage, clearMessages }
}

// ---------------------------------------------------------------------------
// useSendMessage — React Query mutation that calls the orchestrator
// ---------------------------------------------------------------------------

interface SendMessageVars {
  query: string
  patientId?: string
  context?: Record<string, unknown>
  /** Preview to render in the user bubble (set when an image is attached). */
  attachment?: ChatAttachment
}

export function useSendMessage(addMessage: UseChatHistoryReturn['addMessage']) {
  return useMutation<AgentResponse, Error, SendMessageVars>({
    // context is forwarded verbatim (image_data, modality, patient context, …).
    mutationFn: ({ query, patientId, context }) =>
      orchestratorApi.ask(query, patientId, context),

    onMutate: ({ query, attachment }) => {
      addMessage({
        role: 'user',
        content: query,
        timestamp: new Date().toISOString(),
        attachment,
      })
    },

    onSuccess: (response) => {
      addMessage({
        role: 'assistant',
        content: response.response,
        agentType: response.agentUsed,
        timestamp: new Date().toISOString(),
        confidence: response.confidence,
        disclaimer: response.disclaimer,
        reasoning: response.reasoning,
        // Retain the full structured payload + stub flag on the message.
        data: response.data,
        isStub: response.isStub,
      })
    },

    onError: (error) => {
      if (process.env.NODE_ENV !== 'production') {
        console.error('[useSendMessage] orchestrator error:', error)
      }
      addMessage({
        role: 'assistant',
        content:
          'Sorry, I encountered an error processing your request. Please check your connection and try again.',
        agentType: 'orchestrator',
        timestamp: new Date().toISOString(),
      })
    },
  })
}
