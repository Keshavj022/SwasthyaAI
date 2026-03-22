'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { format, parseISO } from 'date-fns'
import { X, ZoomIn, ZoomOut, RotateCw, Download, Trash2, Brain, FileText, ScanLine } from 'lucide-react'
import { toast } from 'sonner'
import { useDeleteDocument } from '@/hooks/useDocuments'
import type { MedicalDocument } from '@/types'

interface DocumentPreviewPanelProps {
  doc: MedicalDocument
  onClose: () => void
}

// ---------------------------------------------------------------------------
// File type detection
// ---------------------------------------------------------------------------

function getDocCategory(doc: MedicalDocument): 'image' | 'pdf' | 'dicom' | 'unknown' {
  if (doc.fileType.startsWith('image/')) return 'image'
  if (doc.fileType === 'application/pdf') return 'pdf'
  if (
    doc.fileType.includes('dicom') ||
    doc.fileName.toLowerCase().endsWith('.dcm') ||
    doc.fileName.toLowerCase().endsWith('.dicom')
  ) {
    return 'dicom'
  }
  return 'unknown'
}

function safeFormatDate(raw: string): string {
  try {
    return format(parseISO(raw), 'd MMM yyyy, HH:mm')
  } catch {
    return 'Unknown date'
  }
}

// ---------------------------------------------------------------------------
// Image viewer
// ---------------------------------------------------------------------------

function ImageViewer({ src, title }: { src: string; title: string }) {
  const [scale, setScale] = useState(1)
  const [rotation, setRotation] = useState(0)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 bg-white flex-shrink-0">
        <button
          type="button"
          onClick={() => setScale((s) => Math.min(s + 0.25, 4))}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
          aria-label="Zoom in"
        >
          <ZoomIn size={14} aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={() => setScale((s) => Math.max(s - 0.25, 0.5))}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
          aria-label="Zoom out"
        >
          <ZoomOut size={14} aria-hidden="true" />
        </button>
        <span className="text-xs text-gray-400 w-10 text-center" aria-live="polite">
          {Math.round(scale * 100)}%
        </span>
        <button
          type="button"
          onClick={() => setRotation((r) => (r + 90) % 360)}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
          aria-label="Rotate 90 degrees"
        >
          <RotateCw size={14} aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={() => { setScale(1); setRotation(0) }}
          className="ml-auto text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded border border-gray-200"
        >
          Reset
        </button>
      </div>
      <div className="flex-1 overflow-auto flex items-center justify-center bg-gray-900 p-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={title}
          style={{ transform: `scale(${scale}) rotate(${rotation}deg)`, transition: 'transform 0.2s' }}
          className="max-w-full max-h-full object-contain"
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// PDF viewer
// ---------------------------------------------------------------------------

function PDFViewer({ src, title }: { src: string; title: string }) {
  return (
    <iframe
      src={src}
      title={title}
      className="w-full h-full border-0"
    />
  )
}

// ---------------------------------------------------------------------------
// DICOM placeholder
// ---------------------------------------------------------------------------

function DICOMPlaceholder({ doc }: { doc: MedicalDocument }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-gray-900">
      <ScanLine size={64} className="text-teal-400 mb-4" aria-hidden="true" />
      <p className="text-white font-semibold text-lg mb-1">{doc.title}</p>
      <p className="text-gray-400 text-sm mb-2">DICOM File · {doc.fileName}</p>
      <p className="text-gray-500 text-xs mb-6">
        Native DICOM rendering requires a dedicated viewer.
      </p>
      <a
        href={doc.url}
        download={doc.fileName}
        className="px-4 py-2 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700"
      >
        Download for DICOM Viewer
      </a>
      <p className="text-gray-600 text-xs mt-4">Open in Horos, OsiriX, or RadiAnt DICOM Viewer</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function DocumentPreviewPanel({ doc, onClose }: DocumentPreviewPanelProps) {
  const router = useRouter()
  const { mutate: deleteDoc, isPending: deleting } = useDeleteDocument()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [analyzingAI, setAnalyzingAI] = useState(false)
  const deleteTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const analyzeAbortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      if (deleteTimeoutRef.current !== null) {
        clearTimeout(deleteTimeoutRef.current)
      }
      analyzeAbortRef.current?.abort()
    }
  }, [])

  const category = getDocCategory(doc)
  const uploadDate = safeFormatDate(doc.uploadedAt)

  function handleDelete() {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true)
      deleteTimeoutRef.current = setTimeout(() => setShowDeleteConfirm(false), 4000)
      return
    }
    deleteDoc(
      { documentId: doc.id, patientId: doc.patientId },
      {
        onSuccess: () => {
          toast.success('Document deleted')
          onClose()
        },
        onError: () => toast.error('Failed to delete document'),
      }
    )
  }

  async function handleAnalyzeWithAI() {
    setAnalyzingAI(true)
    const controller = new AbortController()
    analyzeAbortRef.current = controller
    const token = typeof window !== 'undefined' ? localStorage.getItem('swasthya_token') : null
    try {
      const res = await fetch(doc.url, {
        signal: controller.signal,
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result as string
          resolve(result.split(',')[1] ?? result)
        }
        reader.onerror = () => reject(new Error('Failed to read file'))
        reader.readAsDataURL(blob)
      })
      sessionStorage.setItem(
        'pendingImageAnalysis',
        JSON.stringify({
          base64,
          mimeType: doc.fileType,
          fileName: doc.fileName,
          query: `Please analyze this medical image: ${doc.title || doc.fileName}`,
        })
      )
      router.push('/chat')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      if (process.env.NODE_ENV !== 'production') {
        console.error('[DocumentPreviewPanel] handleAnalyzeWithAI error:', err)
      }
      toast.error('Failed to prepare image for analysis. Please try again.')
    } finally {
      setAnalyzingAI(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-gray-100 flex-shrink-0">
        <div className="flex-1 min-w-0 pr-3">
          <p className="font-semibold text-gray-900 truncate">{doc.title || doc.fileName}</p>
          <p className="text-xs text-gray-500 mt-0.5 truncate">{doc.fileName}</p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 font-medium capitalize">
              {doc.documentType.replace(/_/g, ' ')}
            </span>
            <span className="text-[10px] text-gray-400">{uploadDate}</span>
          </div>
          {doc.tags.length > 0 && (
            <div className="flex gap-1 mt-1.5 flex-wrap">
              {doc.tags.map((tag) => (
                <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 flex-shrink-0"
          aria-label="Close preview"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 bg-gray-50 flex-wrap flex-shrink-0">
        {(category === 'image' || category === 'dicom') && (
          <button
            type="button"
            onClick={handleAnalyzeWithAI}
            disabled={analyzingAI}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-teal-600 text-white
                        hover:bg-teal-700 disabled:opacity-50 transition-colors font-medium"
          >
            <Brain size={12} aria-hidden="true" />
            {analyzingAI ? 'Preparing...' : 'Analyze with AI'}
          </button>
        )}
        <a
          href={doc.url}
          download={doc.fileName}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-gray-200
                      text-gray-600 hover:bg-gray-100 transition-colors"
          aria-label={`Download ${doc.fileName}`}
        >
          <Download size={12} aria-hidden="true" /> Download
        </a>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ml-auto ${
            showDeleteConfirm
              ? 'border-red-300 bg-red-50 text-red-600 hover:bg-red-100'
              : 'border-gray-200 text-gray-400 hover:text-red-500 hover:border-red-200'
          }`}
          aria-label={showDeleteConfirm ? 'Confirm deletion' : 'Delete document'}
        >
          <Trash2 size={12} aria-hidden="true" />
          {showDeleteConfirm ? 'Confirm delete?' : 'Delete'}
        </button>
      </div>

      {/* Viewer area */}
      <div className="flex-1 overflow-hidden min-h-0">
        {category === 'image' && (
          <ImageViewer src={doc.url} title={doc.title || doc.fileName} />
        )}
        {category === 'pdf' && (
          <PDFViewer src={doc.url} title={doc.title || doc.fileName} />
        )}
        {category === 'dicom' && <DICOMPlaceholder doc={doc} />}
        {category === 'unknown' && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <FileText size={48} className="text-gray-300 mb-3" aria-hidden="true" />
            <p className="text-sm text-gray-500">Preview not available for this file type.</p>
            <a
              href={doc.url}
              download={doc.fileName}
              className="mt-4 text-xs text-teal-600 hover:underline"
            >
              Download file
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
