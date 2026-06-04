'use client'

import { useMemo, useState } from 'react'
import {
  FileText,
  FileImage,
  ScanLine,
  File as FileIcon,
  LayoutGrid,
  List as ListIcon,
  MoreVertical,
  Download,
  Trash2,
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/ui/EmptyState'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import type { DocumentVM } from '@/hooks/useDocuments'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function formatBytes(bytes: number): string {
  if (!bytes) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  let val = bytes
  let i = 0
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024
    i++
  }
  return `${val.toFixed(val >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

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

export function isImageDoc(d: DocumentVM): boolean {
  return d.mimeType.startsWith('image/') || /\.(jpe?g|png|gif|webp)$/i.test(d.fileName)
}
export function isPdfDoc(d: DocumentVM): boolean {
  return d.mimeType === 'application/pdf' || /\.pdf$/i.test(d.fileName)
}
export function isDicomDoc(d: DocumentVM): boolean {
  return (
    d.mimeType === 'application/dicom' ||
    /\.(dcm|dicom)$/i.test(d.fileName) ||
    d.documentType === 'imaging' && /\.dcm$/i.test(d.fileName)
  )
}

function DocIcon({ doc, className }: { doc: DocumentVM; className?: string }) {
  if (isImageDoc(doc)) return <FileImage className={className} />
  if (isDicomDoc(doc)) return <ScanLine className={className} />
  if (isPdfDoc(doc)) return <FileText className={className} />
  return <FileIcon className={className} />
}

// Filter tab → document_type values it matches
const FILTERS: { key: string; label: string; match: (d: DocumentVM) => boolean }[] = [
  { key: 'all', label: 'All', match: () => true },
  { key: 'xray', label: 'X-Rays', match: (d) => /xray|x-ray|mri|ct|imaging/i.test(d.documentType) || isDicomDoc(d) },
  { key: 'report', label: 'Reports', match: (d) => /lab_report|report|discharge|clinical_note/i.test(d.documentType) },
  { key: 'prescription', label: 'Prescriptions', match: (d) => /prescription/i.test(d.documentType) },
  { key: 'other', label: 'Other', match: (d) => /other/i.test(d.documentType) || !d.documentType },
]

type SortKey = 'newest' | 'oldest' | 'name'

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface DocumentGridProps {
  documents: DocumentVM[]
  isLoading: boolean
  isError: boolean
  selectedId?: string
  searchTerm: string
  onSelect: (doc: DocumentVM) => void
  onDownload: (doc: DocumentVM) => void
  onDelete: (doc: DocumentVM) => void
  onUploadClick?: () => void
}

export function DocumentGrid({
  documents,
  isLoading,
  isError,
  selectedId,
  searchTerm,
  onSelect,
  onDownload,
  onDelete,
  onUploadClick,
}: DocumentGridProps) {
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState<SortKey>('newest')

  const visible = useMemo(() => {
    const f = FILTERS.find((x) => x.key === filter) ?? FILTERS[0]
    const term = searchTerm.trim().toLowerCase()
    let list = documents.filter(f.match)
    if (term) {
      list = list.filter(
        (d) =>
          d.title.toLowerCase().includes(term) ||
          d.fileName.toLowerCase().includes(term) ||
          d.tags.some((t) => t.toLowerCase().includes(term))
      )
    }
    const sorted = [...list]
    sorted.sort((a, b) => {
      if (sort === 'name') return a.title.localeCompare(b.title)
      const da = new Date(a.uploadedAt).getTime()
      const db = new Date(b.uploadedAt).getTime()
      return sort === 'newest' ? db - da : da - db
    })
    return sorted
  }, [documents, filter, sort, searchTerm])

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Toolbar: filter tabs + sort + view toggle */}
      <div className="flex items-center justify-between gap-3 flex-wrap mb-3">
        <div className="flex items-center gap-1 flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                'text-xs px-3 py-1.5 rounded-full border transition-colors',
                filter === f.key
                  ? 'bg-teal-600 text-white border-teal-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-teal-300 hover:text-teal-700'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="text-xs rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-gray-600
                       focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="name">Name</option>
          </select>

          <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setView('grid')}
              className={cn('p-1.5', view === 'grid' ? 'bg-teal-50 text-teal-700' : 'text-gray-400 hover:text-gray-600')}
              title="Grid view"
            >
              <LayoutGrid size={15} />
            </button>
            <button
              onClick={() => setView('list')}
              className={cn('p-1.5 border-l border-gray-200', view === 'list' ? 'bg-teal-50 text-teal-700' : 'text-gray-400 hover:text-gray-600')}
              title="List view"
            >
              <ListIcon size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        {isLoading ? (
          <div className={view === 'grid' ? 'grid grid-cols-2 sm:grid-cols-3 gap-3' : 'space-y-2'}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className={view === 'grid' ? 'h-40 rounded-xl' : 'h-14 rounded-lg'} />
            ))}
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center text-sm text-red-600">
            Failed to load documents. Check your connection and try again.
          </div>
        ) : visible.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-6 h-6" />}
            title={searchTerm ? 'No matching documents' : 'No documents yet'}
            description={
              searchTerm
                ? 'Try a different search term or filter.'
                : 'Upload a lab report, prescription, or scan to get started.'
            }
            action={onUploadClick ? { label: 'Upload document', onClick: onUploadClick } : undefined}
          />
        ) : view === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {visible.map((doc) => (
              <GridCard
                key={doc.id}
                doc={doc}
                selected={doc.id === selectedId}
                onSelect={() => onSelect(doc)}
                onDownload={() => onDownload(doc)}
                onDelete={() => onDelete(doc)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {visible.map((doc) => (
              <ListRow
                key={doc.id}
                doc={doc}
                selected={doc.id === selectedId}
                onSelect={() => onSelect(doc)}
                onDownload={() => onDownload(doc)}
                onDelete={() => onDelete(doc)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Card / Row
// ---------------------------------------------------------------------------

interface ItemProps {
  doc: DocumentVM
  selected: boolean
  onSelect: () => void
  onDownload: () => void
  onDelete: () => void
}

function ContextMenu({ onDownload, onDelete }: { onDownload: () => void; onDelete: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className="p-1 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100"
          title="More actions"
        >
          <MoreVertical size={15} />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onDownload() }}>
          <Download size={14} className="mr-2" /> Download
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="text-red-600 focus:text-red-600"
        >
          <Trash2 size={14} className="mr-2" /> Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function GridCard({ doc, selected, onSelect, onDownload, onDelete }: ItemProps) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'group relative flex flex-col text-left rounded-xl border bg-white overflow-hidden transition-all',
        selected ? 'border-teal-500 ring-2 ring-teal-200' : 'border-gray-200 hover:border-teal-300 hover:shadow-sm'
      )}
    >
      {/* Thumbnail / icon area */}
      <div className="h-24 flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 text-teal-600">
        <DocIcon doc={doc} className="w-9 h-9" />
      </div>
      <div className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
        <ContextMenu onDownload={onDownload} onDelete={onDelete} />
      </div>
      <div className="p-2.5">
        <p className="text-xs font-medium text-gray-900 truncate" title={doc.title}>
          {doc.title}
        </p>
        <p className="text-[11px] text-gray-400 truncate">{doc.fileName}</p>
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[11px] text-gray-400">{formatBytes(doc.fileSize)}</span>
          <span className="text-[11px] text-gray-400">{formatDate(doc.uploadedAt)}</span>
        </div>
      </div>
    </button>
  )
}

function ListRow({ doc, selected, onSelect, onDownload, onDelete }: ItemProps) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'group w-full flex items-center gap-3 rounded-lg border bg-white px-3 py-2.5 text-left transition-colors',
        selected ? 'border-teal-500 ring-1 ring-teal-200' : 'border-gray-200 hover:border-teal-300'
      )}
    >
      <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center text-teal-600">
        <DocIcon doc={doc} className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
        <p className="text-xs text-gray-400 truncate">{doc.fileName}</p>
      </div>
      <span className="text-xs text-gray-400 hidden sm:block">{formatBytes(doc.fileSize)}</span>
      <span className="text-xs text-gray-400 hidden md:block">{formatDate(doc.uploadedAt)}</span>
      <div className="opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
        <ContextMenu onDownload={onDownload} onDelete={onDelete} />
      </div>
    </button>
  )
}
