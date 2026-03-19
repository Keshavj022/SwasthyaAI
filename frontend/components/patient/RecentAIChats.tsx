'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { MessageCircle, ChevronRight, Bot } from 'lucide-react'
import EmptyState from '@/components/ui/EmptyState'
import { useAuth } from '@/hooks/useAuth'
import type { Message } from '@/types'

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function RecentAIChats() {
  const router = useRouter()
  const { user } = useAuth()
  const [chats, setChats] = useState<Message[]>([])

  useEffect(() => {
    if (!user) return
    try {
      const raw = localStorage.getItem(`swasthya_chat_${user.id}`)
      if (raw) {
        const msgs: Message[] = JSON.parse(raw)
        setChats(msgs.filter((m) => m.role === 'user').slice(-3).reverse())
      }
    } catch {
      // ignore parse errors
    }
  }, [user?.id])

  if (!user) return null

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">Recent AI Chats</h2>
        <Link
          href="/chat"
          className="text-xs text-teal-600 font-medium hover:underline flex items-center gap-0.5"
        >
          Open chat <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {chats.length === 0 ? (
        <EmptyState
          icon={<MessageCircle className="w-6 h-6" />}
          title="No recent chats"
          description="Ask SwasthyaAI anything about your health."
          action={{ label: 'Start chatting', onClick: () => router.push('/chat') }}
        />
      ) : (
        <div className="space-y-2">
          {chats.map((msg) => (
            <div key={msg.id} className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
              <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5 text-teal-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-800 truncate">{msg.content}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-400">{timeAgo(msg.timestamp)}</span>
                  {msg.agentType && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-teal-50 text-teal-600 font-medium">
                      {msg.agentType}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
