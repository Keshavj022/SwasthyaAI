'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  X,
  Download,
  Trash2,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Sparkles,
  ScanLine,
  FileQuestion,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { useDocumentBlobUrl } from '@/hooks/useDocuments'
import type { DocumentVM } from '@/hooks/useDocuments'
import { formatBytes, isImageDoc, isPdfDoc, isDicomDoc } from './DocumentGrid'

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return ''
  }
}

interface DocumentPreviewPanelProps {
  doc: DocumentVM | null
  patientLabel: string
  onClose: () => void
  onDownload: (doc: DocumentVM) => void
  onDelete: (doc: DocumentVM) => void
}

export function DocumentPreviewPanel({
  doc,
  patientLabel,
  onClose,
  onDownload,
  onDelete,
}: DocumentPreviewPanelProps) {
  const router = useRouter()
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const isImage = !!doc && isImageDoc(doc)
  const isPdf = !!doc && isPdfDoc(doc)
  const isDicom = !!doc && isDicomDoc(doc)

  // Only fetch the blob for renderable types (image / pdf).
  const needsBlob = !!doc && (isImage || isPdf)
  const { data: blob, isLoading: blobLoading, isError: blobError } = useDocumentBlobUrl(
    doc?.id ?? null,
    needsBlob
  )

  // Reset transform when switching documents.
  useEffect(() => {
    setZoom(1)
    setRotation(0)
    setConfirmDelete(false)
  }, [doc?.id])

  // Revoke object URL on unmount / change to avoid leaks.
  useEffect(() => {
    const url = blob?.objectUrl
    return () => {
      if (url) URL.revokeObjectURL(url)
    }
  }, [blob?.objectUrl])

  if (!doc) {
    return (
      <aside className="hidden lg:flex w-[40%] max-w-md border-l border-gray-200 bg-white flex-col items-center justify-center text-center p-8">
        <FileQuestion className="w-10 h-10 text-gray-300 mb-3" />
        <p className="text-sm font-medium text-gray-500">No document selected</p>
        <p className="text-xs text-gray-400 mt-1">Select a document to preview it here.</p>
      </aside>
    )
  }

  function handleAnalyze() {
    if (!doc) return
    // Route to chat; the chat page reads ?analyzeDoc=<id> and attaches the
    // image via the authenticated blob fetch before sending to the
    // image_analysis agent.
    router.push(`/chat?analyzeDoc=${encodeURIComponent(doc.id)}`)
  }

  return (
    <aside className="w-full lg:w-[40%] lg:max-w-md border-l border-gray-200 bg-white flex flex-col min-h-0">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate" title={doc.title}>
            {doc.title}
          </p>
          <p className="text-xs text-gray-400 truncate">{doc.fileName}</p>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <Badge variant="secondary" className="text-[10px] capitalize">
              {doc.documentType.replace(/_/g, ' ')}
            </Badge>
            <span className="text-[11px] text-gray-400">{formatBytes(doc.fileSize)}</span>
            <span className="text-[11px] text-gray-400">· {formatDate(doc.uploadedAt)}</span>
          </div>
        </div>
        <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600" title="Close preview">
          <X size={16} />
        </button>
      </div>

      {/* Tags */}
      {doc.tags.length > 0 && (
        <div className="px-4 pt-2 flex flex-wrap gap-1">
          {doc.tags.map((t) => (
            <span key={t} className="px-1.5 py-0.5 rounded bg-teal-50 text-teal-700 text-[10px]">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Preview body */}
      <div className="flex-1 min-h-0 overflow-auto bg-gray-50 p-3 flex items-center justify-center">
        {isDicom ? (
          <DicomPlaceholder doc={doc} patientLabel={patientLabel} onDownload={() => onDownload(doc)} />
        ) : blobLoading ? (
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span className="text-xs">Loading preview…</span>
          </div>
        ) : blobError || !blob ? (
          <div className="text-center text-xs text-red-500">
            Could not load preview.
            <button onClick={() => onDownload(doc)} className="block mx-auto mt-2 text-teal-600 underline">
              Download instead
            </button>
          </div>
        ) : isImage ? (
          <div className="overflow-auto max-w-full max-h-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={blob.objectUrl}
              alt={doc.title}
              style={{ transform: `scale(${zoom}) rotate(${rotation}deg)`, transition: 'transform 0.15s' }}
              className="max-w-none rounded shadow-sm origin-center"
            />
          </div>
        ) : isPdf ? (
          <iframe
            src={blob.objectUrl}
            title={doc.title}
            className="w-full h-full min-h-[400px] rounded border border-gray-200 bg-white"
          />
        ) : (
          <div className="text-center text-xs text-gray-500">
            Preview not available for this file type.
            <button onClick={() => onDownload(doc)} className="block mx-auto mt-2 text-teal-600 underline">
              Download to view
            </button>
          </div>
        )}
      </div>

      {/* Image controls */}
      {isImage && blob && (
        <div className="flex items-center justify-center gap-1 px-4 py-2 border-t border-gray-100">
          <IconBtn label="Zoom out" onClick={() => setZoom((z) => Math.max(0.25, +(z - 0.25).toFixed(2)))}>
            <ZoomOut size={15} />
          </IconBtn>
          <span className="text-xs text-gray-500 w-10 text-center">{Math.round(zoom * 100)}%</span>
          <IconBtn label="Zoom in" onClick={() => setZoom((z) => Math.min(4, +(z + 0.25).toFixed(2)))}>
            <ZoomIn size={15} />
          </IconBtn>
          <span className="w-px h-4 bg-gray-200 mx-1" />
          <IconBtn label="Rotate" onClick={() => setRotation((r) => (r + 90) % 360)}>
            <RotateCw size={15} />
          </IconBtn>
        </div>
      )}

      {/* Footer actions */}
      <div className="px-4 py-3 border-t border-gray-100 flex items-center gap-2">
        <Button variant="outline" size="sm" className="flex-1" onClick={() => onDownload(doc)}>
          <Download size={14} className="mr-1.5" /> Download
        </Button>
        {(isImage || isDicom) && (
          <Button size="sm" className="flex-1" onClick={handleAnalyze} disabled={isDicom}>
            <Sparkles size={14} className="mr-1.5" /> Analyze with AI
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="text-red-600 hover:text-red-700 hover:bg-red-50 px-2"
          onClick={() => setConfirmDelete(true)}
          title="Delete document"
        >
          <Trash2 size={15} />
        </Button>
      </div>

      {/* Delete confirm */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete document?</DialogTitle>
            <DialogDescription>
              &quot;{doc.title}&quot; will be permanently removed. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setConfirmDelete(false)
                onDelete(doc)
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </aside>
  )
}

function IconBtn({
  children,
  label,
  onClick,
}: {
  children: React.ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className="p-1.5 rounded-md text-gray-500 hover:text-teal-700 hover:bg-teal-50 transition-colors"
    >
      {children}
    </button>
  )
}

function DicomPlaceholder({
  doc,
  patientLabel,
  onDownload,
}: {
  doc: DocumentVM
  patientLabel: string
  onDownload: () => void
}) {
  return (
    <div className="flex flex-col items-center text-center max-w-xs rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center text-teal-300 mb-3">
        <ScanLine className="w-8 h-8" />
      </div>
      <p className="text-sm font-semibold text-gray-900">DICOM medical scan</p>
      <div className="text-xs text-gray-500 mt-3 space-y-1 w-full">
        <div className="flex justify-between"><span className="text-gray-400">Patient</span><span className="font-medium text-gray-700 truncate ml-2">{patientLabel}</span></div>
        <div className="flex justify-between"><span className="text-gray-400">Modality</span><span className="font-medium text-gray-700 capitalize">{doc.documentType.replace(/_/g, ' ')}</span></div>
        <div className="flex justify-between"><span className="text-gray-400">Date</span><span className="font-medium text-gray-700">{formatDate(doc.documentDate ?? doc.uploadedAt)}</span></div>
      </div>
      <Button size="sm" className="mt-4 w-full" onClick={onDownload}>
        <Download size={14} className="mr-1.5" /> Download for DICOM viewer
      </Button>
      <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
        Open in Horos, OsiriX, or RadiAnt DICOM Viewer.
      </p>
    </div>
  )
}
