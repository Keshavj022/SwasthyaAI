"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import ConfidenceMeter from "@/components/ConfidenceMeter";
import DisclaimerBox from "@/components/DisclaimerBox";
import { sendChatMessage } from "@/lib/api";
import type { ChatResponseData, QueryResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  // assistant-only fields
  confidence?: { score: number; level: string } | null;
  disclaimer?: string;
  agent?: string | null;
  emergency?: boolean | null;
  alerts?: string[];
  recommendations?: string[];
  error?: string;
}

type ConfidenceLevel = "high" | "moderate" | "low" | "very_low";

type DisclaimerCategory =
  | "general"
  | "diagnostic"
  | "image_analysis"
  | "medication"
  | "emergency"
  | "voice";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isConfidenceLevel(v: string): v is ConfidenceLevel {
  return ["high", "moderate", "low", "very_low"].includes(v);
}

function disclaimerCategoryForAgent(
  agent: string | null | undefined
): DisclaimerCategory {
  if (!agent) return "general";
  if (agent.includes("diagnostic")) return "diagnostic";
  if (agent.includes("image")) return "image_analysis";
  if (agent.includes("drug") || agent.includes("medication"))
    return "medication";
  if (agent.includes("triage")) return "emergency";
  if (agent.includes("voice")) return "voice";
  return "general";
}

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const USER_ID = "patient_local";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function UserBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] rounded-2xl rounded-br-sm bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm">
        {message.content}
        <p className="mt-1 text-[10px] text-blue-200 text-right">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

function AssistantBubble({ message }: { message: ChatMessage }) {
  const level = message.confidence?.level;

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] space-y-2">
        {/* Emergency banner */}
        {message.emergency && (
          <SafetyBanner
            level="emergency"
            title="Emergency Indicators Detected"
            description="This situation may require immediate medical attention."
          />
        )}

        {/* Error state */}
        {message.error && (
          <SafetyBanner
            level="warning"
            title="Request Failed"
            description={message.error}
          />
        )}

        {/* Main bubble */}
        <div className="rounded-2xl rounded-bl-sm bg-white border border-gray-200 px-4 py-2.5 shadow-sm">
          {/* Agent tag + confidence badge */}
          <div className="flex items-center gap-2 mb-1.5">
            {message.agent && (
              <span className="text-[10px] font-medium uppercase tracking-wider text-gray-400">
                {message.agent.replace(/_/g, " ")}
              </span>
            )}
            {message.confidence && level && isConfidenceLevel(level) && (
              <ConfidenceMeter
                score={message.confidence.score}
                level={level}
                compact
              />
            )}
          </div>

          {/* Response body */}
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>

          {/* Alerts */}
          {message.alerts && message.alerts.length > 0 && (
            <div className="mt-2 space-y-1">
              {message.alerts.map((alert, i) => (
                <div
                  key={i}
                  className="flex items-start gap-1.5 text-xs text-amber-700 bg-amber-50 rounded px-2 py-1"
                >
                  <svg
                    aria-hidden="true"
                    className="w-3.5 h-3.5 shrink-0 mt-0.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                    />
                  </svg>
                  {alert}
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {message.recommendations && message.recommendations.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-xs text-gray-600">
              {message.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-blue-400 mt-0.5 shrink-0">
                    &#8227;
                  </span>
                  {rec}
                </li>
              ))}
            </ul>
          )}

          {/* Timestamp */}
          <p className="mt-1.5 text-[10px] text-gray-400">
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>

        {/* Disclaimer pinned beneath bubble */}
        {message.disclaimer && (
          <DisclaimerBox
            text={message.disclaimer}
            category={disclaimerCategoryForAgent(message.agent)}
            collapsible
          />
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div
      className="flex justify-start"
      role="status"
      aria-label="Agent is typing"
    >
      <div className="rounded-2xl rounded-bl-sm bg-white border border-gray-200 px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [isOnline, setIsOnline] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Online / offline listener ──────────────────────────────────────────
  useEffect(() => {
    const update = () => setIsOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    update();
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  // ── Auto-scroll on new messages ────────────────────────────────────────
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, sending]);

  // ── Send handler ───────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = {
      id: makeId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    const result = await sendChatMessage(text, USER_ID);

    let assistantMsg: ChatMessage;

    if (result.ok) {
      const qr: QueryResponse<ChatResponseData> = result.data;
      const responseText =
        typeof qr.data.response === "string"
          ? qr.data.response
          : JSON.stringify(qr.data, null, 2);

      assistantMsg = {
        id: makeId(),
        role: "assistant",
        content: responseText,
        timestamp: new Date(),
        confidence: qr.confidence,
        disclaimer: qr.disclaimer,
        agent: qr.agent,
        emergency: qr.emergency,
        alerts: qr.data.alerts,
        recommendations: qr.data.recommendations,
      };
    } else {
      assistantMsg = {
        id: makeId(),
        role: "assistant",
        content: result.offline
          ? "The system is currently offline. Your message was not delivered."
          : "Something went wrong while processing your request.",
        timestamp: new Date(),
        error: result.error,
      };
    }

    setMessages((prev) => [...prev, assistantMsg]);
    setSending(false);

    requestAnimationFrame(() => inputRef.current?.focus());
  }, [input, sending]);

  const canSend = input.trim().length > 0 && !sending;

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <PageContainer
      title="Chat"
      description="Medical Q&A powered by local language models. All data stays on-device."
      icon="💬"
    >
      <div
        className="bg-white rounded-lg border border-gray-200 shadow-sm flex flex-col"
        style={{ height: "calc(100vh - 280px)" }}
      >
        {/* ── Offline banner ─────────────────────────────────────── */}
        {!isOnline && (
          <div className="px-4 pt-3">
            <SafetyBanner
              level="warning"
              title="You are offline"
              description="Messages cannot be sent while the network is unavailable. They will remain in this session and you can retry once connectivity is restored."
            />
          </div>
        )}

        {/* ── Messages area ──────────────────────────────────────── */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        >
          {messages.length === 0 && !sending && (
            <div className="flex-1 flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <p className="text-5xl mb-4">💬</p>
                <p className="text-lg font-medium">No messages yet</p>
                <p className="text-sm mt-1">
                  Start a conversation with the health support agent.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) =>
            msg.role === "user" ? (
              <UserBubble key={msg.id} message={msg} />
            ) : (
              <AssistantBubble key={msg.id} message={msg} />
            )
          )}

          {sending && <TypingIndicator />}
        </div>

        {/* ── Input area ─────────────────────────────────────────── */}
        <div className="border-t border-gray-200 px-4 py-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-3"
          >
            <label htmlFor="chat-input" className="sr-only">
              Message
            </label>
            <input
              ref={inputRef}
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                isOnline
                  ? "Type your message..."
                  : "Offline — cannot send messages"
              }
              disabled={!isOnline || sending}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!canSend || !isOnline}
              aria-label="Send message"
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg
                className="w-4 h-4"
                aria-hidden="true"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
                />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </PageContainer>
  );
}
