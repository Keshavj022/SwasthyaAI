'use client'

import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { orchestratorApi } from '@/lib/api'
import type { Message, AgentResponse } from '@/types'

let messageCounter = 0
function nextId() {
  return `msg-${++messageCounter}-${Date.now()}`
}

interface UseChatHistoryReturn {
  messages: Message[]
  addMessage: (msg: Omit<Message, 'id'>) => Message
  clearMessages: () => void
}

export function useChatHistory(): UseChatHistoryReturn {
  const [messages, setMessages] = useState<Message[]>([])

  const addMessage = useCallback((msg: Omit<Message, 'id'>): Message => {
    const full: Message = { ...msg, id: nextId() }
    setMessages((prev) => [...prev, full])
    return full
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, addMessage, clearMessages }
}

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
        agentType: 'user',
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
      })
    },
  })
}
