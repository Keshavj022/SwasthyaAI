'use client'

import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { orchestratorApi } from '@/lib/api'
import type { Message, AgentResponse } from '@/types'

let messageCounter = 0
function nextId() {
  return `msg-${++messageCounter}-${Date.now()}`
}

// ---------------------------------------------------------------------------
// useChatHistory — message state with localStorage persistence
// ---------------------------------------------------------------------------

interface UseChatHistoryReturn {
  messages: Message[]
  addMessage: (msg: Omit<Message, 'id'>) => Message
  clearMessages: () => void
}

export function useChatHistory(userId?: string): UseChatHistoryReturn {
  const storageKey = userId ? `swasthya_chat_${userId}` : null

  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === 'undefined' || !storageKey) return []
    try {
      const stored = localStorage.getItem(storageKey)
      return stored ? (JSON.parse(stored) as Message[]) : []
    } catch {
      return []
    }
  })

  const addMessage = useCallback(
    (msg: Omit<Message, 'id'>): Message => {
      const full: Message = { ...msg, id: nextId() }
      setMessages((prev) => {
        const next = [...prev, full]
        if (typeof window !== 'undefined' && storageKey) {
          localStorage.setItem(storageKey, JSON.stringify(next))
        }
        return next
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
}

export function useSendMessage(addMessage: UseChatHistoryReturn['addMessage']) {
  return useMutation<AgentResponse, Error, SendMessageVars>({
    mutationFn: ({ query, patientId, context }) =>
      orchestratorApi.ask(query, patientId, context),

    onMutate: ({ query }) => {
      addMessage({
        role: 'user',
        content: query,
        timestamp: new Date().toISOString(),
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
      })
    },

    onError: () => {
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please check your connection and try again.',
        agentType: 'orchestrator',
        timestamp: new Date().toISOString(),
      })
    },
  })
}
