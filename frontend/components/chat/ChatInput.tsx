'use client'

import { useState, useRef, useEffect, useCallback, type KeyboardEvent, type ChangeEvent } from 'react'
import { Send, Paperclip, X, Mic, MicOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

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
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

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

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop()
    }
  }, [])

  const startRecording = useCallback(async () => {
    if (isRecording) {
      stopRecording()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunksRef.current = []
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setIsRecording(false)

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        if (audioBlob.size === 0) return

        setIsTranscribing(true)
        try {
          const reader = new FileReader()
          const base64 = await new Promise<string>((resolve, reject) => {
            reader.onload = () => {
              const result = reader.result as string
              // strip the data URL prefix
              resolve(result.split(',')[1] ?? result)
            }
            reader.onerror = reject
            reader.readAsDataURL(audioBlob)
          })

          const res = await fetch('/api/orchestrator/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              message: 'transcribe voice input',
              context: {
                agent: 'voice_interaction',
                mode: 'voice_query',
                audio_data: base64,
                language: 'en-US',
              },
            }),
          })

          if (!res.ok) throw new Error('Transcription request failed')

          const data = await res.json()
          const transcription: string =
            data?.data?.transcription ?? data?.data?.text ?? ''

          if (transcription && !transcription.toLowerCase().includes('unavailable')) {
            setText((prev) => (prev ? prev + ' ' + transcription : transcription))
            textareaRef.current?.focus()
          } else {
            toast.error('Voice transcription unavailable — MedASR model not loaded')
          }
        } catch {
          toast.error('Voice transcription failed')
        } finally {
          setIsTranscribing(false)
        }
      }

      recorder.start()
      setIsRecording(true)
    } catch {
      toast.error('Microphone access denied or unavailable')
    }
  }, [isRecording, stopRecording])

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
        {/* Paperclip (file upload) */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 p-2 text-gray-400 hover:text-teal-600 transition-colors rounded-lg hover:bg-gray-100"
          title="Attach image or PDF"
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

        {/* Voice input button (MedASR) */}
        <button
          type="button"
          onClick={startRecording}
          disabled={disabled || isTranscribing}
          className={[
            'flex-shrink-0 p-2 transition-colors rounded-lg',
            isRecording
              ? 'text-red-500 hover:text-red-600 bg-red-50 hover:bg-red-100 animate-pulse'
              : isTranscribing
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-400 hover:text-teal-600 hover:bg-gray-100',
          ].join(' ')}
          title={isRecording ? 'Stop recording' : isTranscribing ? 'Transcribing…' : 'Voice input (MedASR)'}
        >
          {isTranscribing ? (
            <Loader2 size={18} className="animate-spin" />
          ) : isRecording ? (
            <MicOff size={18} />
          ) : (
            <Mic size={18} />
          )}
        </button>

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
