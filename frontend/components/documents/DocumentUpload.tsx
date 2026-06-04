'use client'

import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'
import { UploadCloud, X, FileText, FileImage, ScanLine, File as FileIcon } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useUploadDocument } from '@/hooks/useDocuments'
import { formatBytes } from './DocumentGrid'

const MAX_BYTES = 50 * 1024 * 1024 // 50 MB
const ACCEPT = '.pdf,.jpg,.jpeg,.png,.dcm,.dicom,image/*,application/pdf'
const ACCEPTED_EXT = /\.(pdf|jpe?g|png|dcm|dicom)$/i

// Maps the UI label to a backend document_type slug.
const DOC_TYPES: { value: string; label: string }[] = [
  { value: 'xray', label: 'X-Ray' },
  { value: 'mri', label: 'MRI' },
  { value: 'ct_scan', label: 'CT Scan' },
  { value: 'lab_report', label: 'Lab Report' },
  { value: 'prescription', label: 'Prescription' },
  { value: 'other', label: 'Other' },
]

function fileIcon(file: File) {
  const n = file.name
  if (/\.(dcm|dicom)$/i.test(n)) return <ScanLine className="w-4 h-4 text-teal-600" />
  if (file.type.startsWith('image/')) return <FileImage className="w-4 h-4 text-teal-600" />
  if (file.type === 'application/pdf' || /\.pdf$/i.test(n)) return <FileText className="w-4 h-4 text-teal-600" />
  return <FileIcon className="w-4 h-4 text-teal-600" />
}

interface DocumentUploadProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  patientId: string
  patientLabel: string
}

export function DocumentUpload({ open, onOpenChange, patientId, patientLabel }: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [docType, setDocType] = useState('other')
  const [dragOver, setDragOver] = useState(false)

  const { mutate, isPending, uploadProgress, resetProgress } = useUploadDocument()

  function reset() {
    setFile(null)
    setTitle('')
    setDocType('other')
    resetProgress()
  }

  function selectFile(f: File) {
    if (!ACCEPTED_EXT.test(f.name)) {
      toast.error('Unsupported file type. Use PDF, JPG, PNG, or DICOM.')
      return
    }
    if (f.size > MAX_BYTES) {
      toast.error('File is too large. Maximum size is 50 MB.')
      return
    }
    setFile(f)
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''))
  }

  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (f) selectFile(f)
    e.target.value = ''
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) selectFile(f)
  }

  function handleUpload() {
    if (!file || !patientId) return
    mutate(
      { patientId, file, documentType: docType, title: title.trim() || file.name },
      {
        onSuccess: () => {
          toast.success('Document uploaded')
          reset()
          onOpenChange(false)
        },
        onError: () => {
          toast.error('Upload failed. Please try again.')
        },
      }
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!isPending) {
          if (!o) reset()
          onOpenChange(o)
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload document</DialogTitle>
          <DialogDescription>
            PDF, JPG, PNG, or DICOM up to 50 MB. Uploading for{' '}
            <span className="font-medium text-gray-700">{patientLabel}</span>.
          </DialogDescription>
        </DialogHeader>

        {/* Drop zone */}
        {!file ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed
                        px-6 py-10 cursor-pointer transition-colors ${
                          dragOver ? 'border-teal-500 bg-teal-50' : 'border-gray-300 hover:border-teal-400 hover:bg-gray-50'
                        }`}
          >
            <UploadCloud className="w-8 h-8 text-teal-500" />
            <p className="text-sm font-medium text-gray-700">Click to upload or drag files here</p>
            <p className="text-xs text-gray-400">PDF, JPG, PNG, DICOM · max 50 MB</p>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5">
            <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
              {fileIcon(file)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
              <p className="text-xs text-gray-400">{formatBytes(file.size)}</p>
            </div>
            {!isPending && (
              <button
                onClick={() => setFile(null)}
                className="p-1 text-gray-400 hover:text-gray-600"
                title="Remove"
              >
                <X size={15} />
              </button>
            )}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={handleInputChange}
        />

        {/* Metadata */}
        <div className="grid gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="doc-title">Title</Label>
            <Input
              id="doc-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Chest X-Ray"
              disabled={isPending}
            />
          </div>

          <div className="grid gap-1.5">
            <Label>Document type</Label>
            <Select value={docType} onValueChange={setDocType} disabled={isPending}>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {DOC_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Progress */}
        {isPending && (
          <div className="space-y-1">
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-xs text-gray-400 text-right">{uploadProgress}%</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-1">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || isPending}>
            {isPending ? 'Uploading…' : 'Upload'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
