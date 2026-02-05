"use client"

import { useState } from "react"

/**
 * Categories match the backend safety_wrapper disclaimer mapping:
 *   general | diagnostic | image_analysis | medication | emergency | voice
 */
type DisclaimerCategory =
  | "general"
  | "diagnostic"
  | "image_analysis"
  | "medication"
  | "emergency"
  | "voice"

interface DisclaimerBoxProps {
  /** The raw disclaimer string returned by the backend. */
  text: string
  /**
   * Optional category hint — controls the icon and accent color.
   * Falls back to "general" when omitted.
   */
  category?: DisclaimerCategory
  /**
   * When true the body text is collapsed behind a toggle.
   * Useful when the disclaimer is lengthy or repeated on every result.
   */
  collapsible?: boolean
  /** Override the default collapsed state (only applies when collapsible). */
  defaultOpen?: boolean
}

const accents: Record<
  DisclaimerCategory,
  { border: string; bg: string; text: string; icon: React.ReactNode }
> = {
  general: {
    border: "border-gray-300",
    bg: "bg-gray-50",
    text: "text-gray-700",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-gray-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
      </svg>
    ),
  },
  diagnostic: {
    border: "border-yellow-300",
    bg: "bg-yellow-50",
    text: "text-yellow-800",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-yellow-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
  },
  image_analysis: {
    border: "border-purple-300",
    bg: "bg-purple-50",
    text: "text-purple-800",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-purple-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
      </svg>
    ),
  },
  medication: {
    border: "border-blue-300",
    bg: "bg-blue-50",
    text: "text-blue-800",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
      </svg>
    ),
  },
  emergency: {
    border: "border-red-300",
    bg: "bg-red-50",
    text: "text-red-800",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-red-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
    ),
  },
  voice: {
    border: "border-teal-300",
    bg: "bg-teal-50",
    text: "text-teal-800",
    icon: (
      <svg aria-hidden="true" className="w-4 h-4 text-teal-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
      </svg>
    ),
  },
}

export default function DisclaimerBox({
  text,
  category = "general",
  collapsible = false,
  defaultOpen = false,
}: DisclaimerBoxProps) {
  const [open, setOpen] = useState(defaultOpen)
  const style = accents[category]

  const body = (
    <p className={`text-xs leading-relaxed whitespace-pre-line ${style.text}`}>
      {text}
    </p>
  )

  return (
    <aside
      aria-label="Clinical disclaimer"
      className={`rounded-lg border ${style.border} ${style.bg} overflow-hidden`}
    >
      {collapsible ? (
        <>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-blue-500 rounded-lg"
          >
            {style.icon}
            <span className={`text-xs font-medium flex-1 ${style.text}`}>
              Clinical Disclaimer
            </span>
            <svg
              aria-hidden="true"
              className={`w-4 h-4 transition-transform ${style.text} ${open ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </button>
          {open && <div className="px-4 pb-3">{body}</div>}
        </>
      ) : (
        <div className="flex gap-2 px-4 py-3">
          {style.icon}
          <div className="flex-1 min-w-0">{body}</div>
        </div>
      )}
    </aside>
  )
}
