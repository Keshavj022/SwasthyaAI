'use client'

import { useState, useRef, type DragEvent } from 'react'
import { UploadCloud, X, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { useUploadDocument } from '@/hooks/useDocuments'
import type { UploadDocumentPayload } from '@/lib/api'

const DOCUMENT_TYPES = [
  { value: 'xray',         label: 'X-Ray' },
  { value: 'ct_scan',      label: 'CT Scan' },
  { value: 'mri',          label: 'MRI' },
  { value: 'lab_report',   label: 'Lab Report' },
  { value: 'prescription', label: 'Prescription' },
  { value: 'other',        label: 'Other' },
]

const ACCEPTED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.dcm', '.dicom']
const MAX_SIZE_BYTES = 50 * 1024 * 1024

interface DocumentUploadProps {
  patientId: string
  onSuccess?: () => void
}

export function DocumentUpload({ patientId, onSuccess }: DocumentUploadProps) {
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [docType, setDocType] = useState('other')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const currentReaderRef = useRef<FileReader | null>(null)

  const { mutate: upload, isPending, uploadProgress } = useUploadDocument()

  function validateAndSet(file: File) {
    // Cancel any in-progress FileReader from a previous selection
    if (currentReaderRef.current) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(currentReaderRef.current as any).__cancel?.()
      currentReaderRef.current = null
    }

    if (file.size > MAX_SIZE_BYTES) {
      toast.error('File too large. Maximum size is 50 MB.')
      return
    }
    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    const ok = file.type.startsWith('image/') ||
               file.type === 'application/pdf' ||
               ext === 'dcm' || ext === 'dicom'
    if (!ok) {
      toast.error('Unsupported file type. Use PDF, JPG, PNG, or DICOM.')
      return
    }
    setSelectedFile(file)
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      let cancelled = false
      reader.onload = (e) => {
        if (!cancelled) setPreview(e.target?.result as string)
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(reader as any).__cancel = () => { cancelled = true }
      currentReaderRef.current = reader
      reader.readAsDataURL(file)
    } else {
      setPreview(null)
    }
    // Auto-fill title from filename if empty
    if (!title) {
      setTitle(file.name.replace(/\.[^.]+$/, '').replace(/[_-]/g, ' '))
    }
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(true)
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    // Only clear dragging state when leaving the drop zone entirely, not when
    // moving to a child element within it.
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
      setDragging(false)
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) validateAndSet(file)
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) validateAndSet(file)
    e.target.value = ''
  }

  function handleUpload() {
    if (!selectedFile || !title.trim()) {
      toast.error('Please select a file and enter a title.')
      return
    }
    const payload: UploadDocumentPayload = {
      patientId,
      file: selectedFile,
      documentType: docType,
      title: title.trim(),
      description: description.trim() || undefined,
    }
    upload(payload, {
      onSuccess: () => {
        toast.success('Document uploaded successfully!')
        setSelectedFile(null)
        setPreview(null)
        setTitle('')
        setDescription('')
        setDocType('other')
        onSuccess?.()
      },
      onError: () => toast.error('Upload failed. Please try again.'),
    })
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        role="button"
        aria-label="Upload area: click or drag a file here"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click() }}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
          dragging
            ? 'border-teal-400 bg-teal-50 cursor-copy'
            : selectedFile
            ? 'border-gray-200 bg-gray-50 cursor-default'
            : 'border-gray-200 hover:border-teal-300 hover:bg-gray-50 cursor-pointer'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          className="hidden"
          onChange={handleFileInput}
          aria-hidden="true"
        />

        {selectedFile ? (
          <div className="flex items-center justify-center gap-4">
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="File preview" className="w-20 h-20 object-cover rounded-lg border border-gray-200" />
            ) : (
              <div className="w-20 h-20 rounded-lg border border-gray-200 bg-white flex items-center justify-center">
                <FileText size={32} className="text-gray-400" />
              </div>
            )}
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setPreview(null) }}
                className="mt-2 text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
              >
                <X size={12} /> Remove file
              </button>
            </div>
          </div>
        ) : (
          <>
            <UploadCloud size={36} className="mx-auto text-gray-300 mb-3" aria-hidden="true" />
            <p className="text-sm font-medium text-gray-700">Drop a file here, or click to browse</p>
            <p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG, DICOM · Max 50 MB</p>
          </>
        )}
      </div>

      {/* Form fields */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="doc-type" className="text-xs font-medium text-gray-600 mb-1 block">
            Document Type <span aria-hidden="true">*</span>
          </label>
          <select
            id="doc-type"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="doc-title" className="text-xs font-medium text-gray-600 mb-1 block">
            Title <span aria-hidden="true">*</span>
          </label>
          <input
            id="doc-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Chest X-Ray March 2026"
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>
      </div>

      <div>
        <label htmlFor="doc-description" className="text-xs font-medium text-gray-600 mb-1 block">
          Description (optional)
        </label>
        <input
          id="doc-description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief notes about this document..."
          className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      {/* Progress bar */}
      {isPending && (
        <div role="progressbar" aria-valuenow={uploadProgress ?? 0} aria-valuemin={0} aria-valuemax={100} aria-label="Upload progress">
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-teal-500 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress ?? 0}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1 text-right">{uploadProgress ?? 0}%</p>
        </div>
      )}

      <button
        type="button"
        onClick={handleUpload}
        disabled={!selectedFile || !title.trim() || isPending}
        className="w-full py-2.5 rounded-xl bg-teal-600 text-white text-sm font-semibold
                    hover:bg-teal-700 disabled:opacity-40 transition-colors"
      >
        {isPending ? 'Uploading...' : 'Upload Document'}
      </button>
    </div>
  )
}
