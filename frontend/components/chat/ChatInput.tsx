'use client'

import { useState, useRef, useEffect, type KeyboardEvent, type ChangeEvent } from 'react'
import { Send, Paperclip, X } from 'lucide-react'

interface SelectedFile {
  file: File
  preview: string | null   // data URL for images, null for PDFs
}

interface ChatInputProps {
  onSend: (text: string, file?: File) => void
  disabled?: boolean
  initialValue?: string
  onInitialValueConsumed?: () => void
}

export function ChatInput({
  onSend,
  disabled = false,
  initialValue = '',
  onInitialValueConsumed,
}: ChatInputProps) {
  const [text, setText] = useState('')
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Populate from suggested prompt
  useEffect(() => {
    if (initialValue) {
      setText(initialValue)
      onInitialValueConsumed?.()
      textareaRef.current?.focus()
    }
  }, [initialValue, onInitialValueConsumed])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  }, [text])

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed, selectedFile?.file)
    setText('')
    setSelectedFile(null)
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (ev) => {
        setSelectedFile({ file, preview: ev.target?.result as string })
      }
      reader.readAsDataURL(file)
    } else {
      setSelectedFile({ file, preview: null })
    }

    // Reset input so same file can be re-selected
    e.target.value = ''
  }

  const charCount = text.length
  const showCounter = charCount > 200

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      {/* File preview chip */}
      {selectedFile && (
        <div className="flex items-center gap-2 mb-2">
          {selectedFile.preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={selectedFile.preview}
              alt="preview"
              className="w-10 h-10 rounded object-cover border border-gray-200"
            />
          ) : (
            <div className="px-2 py-1 rounded bg-gray-100 text-xs text-gray-600">
              📄 {selectedFile.file.name}
            </div>
          )}
          <button
            onClick={() => setSelectedFile(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* Paperclip (file upload — Task 09 for full functionality) */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 p-2 text-gray-400 hover:text-teal-600 transition-colors rounded-lg hover:bg-gray-100"
          title="Attach image or PDF (image analysis coming soon)"
          disabled={disabled}
        >
          <Paperclip size={18} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask about symptoms, medications, appointments..."
            rows={1}
            className="w-full resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                       disabled:bg-gray-50 disabled:text-gray-400
                       overflow-y-auto"
            style={{ maxHeight: 120 }}
          />
          {showCounter && (
            <span
              className={`absolute bottom-2 right-2 text-xs ${
                charCount > 500 ? 'text-red-400' : 'text-gray-400'
              }`}
            >
              {charCount}
            </span>
          )}
        </div>

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="flex-shrink-0 p-2.5 rounded-xl bg-teal-600 text-white
                     hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors shadow-sm"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
