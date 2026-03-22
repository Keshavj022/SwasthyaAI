'use client'

import { useState, useMemo } from 'react'
import { format, parseISO } from 'date-fns'
import { LayoutGrid, List, FileText, ScanLine, FlaskConical, Pill, Paperclip } from 'lucide-react'
import { usePatientDocuments } from '@/hooks/useDocuments'
import type { MedicalDocument } from '@/types'

interface DocumentGridProps {
  patientId: string
  selectedId: string | null
  onSelect: (doc: MedicalDocument) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const FILTER_TABS = [
  { label: 'All',            key: 'all' },
  { label: 'X-Rays',        key: 'xray' },
  { label: 'Reports',       key: 'lab_report' },
  { label: 'Prescriptions', key: 'prescription' },
  { label: 'Other',         key: 'other' },
]

const KNOWN_TYPES = ['xray', 'lab_report', 'prescription']

function matchesFilter(doc: MedicalDocument, filter: string): boolean {
  if (filter === 'all') return true
  if (filter === 'other') return !KNOWN_TYPES.includes(doc.documentType)
  return doc.documentType === filter
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function DocTypeIcon({ doc }: { doc: MedicalDocument }) {
  if (doc.fileType.startsWith('image/')) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={doc.url}
        alt={doc.title}
        className="w-full h-full object-cover rounded-lg"
        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
      />
    )
  }
  const iconClass = 'w-8 h-8 text-gray-400'
  if (doc.fileType === 'application/pdf') return <FileText className={iconClass} />
  if (['xray', 'ct_scan', 'mri'].includes(doc.documentType)) return <ScanLine className={iconClass} />
  if (doc.documentType === 'lab_report') return <FlaskConical className={iconClass} />
  if (doc.documentType === 'prescription') return <Pill className={iconClass} />
  return <Paperclip className={iconClass} />
}

function safeFormatDate(raw: string): string {
  try {
    return format(parseISO(raw), 'd MMM yyyy')
  } catch {
    return 'Unknown date'
  }
}

function DocCard({
  doc,
  selected,
  onSelect,
  gridView,
}: {
  doc: MedicalDocument
  selected: boolean
  onSelect: () => void
  gridView: boolean
}) {
  const date = safeFormatDate(doc.uploadedAt)
  const size = formatFileSize(doc.fileSize)

  if (gridView) {
    return (
      <button
        onClick={onSelect}
        aria-label={doc.title || doc.fileName}
        className={`w-full text-left rounded-xl border transition-all overflow-hidden ${
          selected
            ? 'border-teal-500 ring-2 ring-teal-200'
            : 'border-gray-200 hover:border-teal-300 hover:shadow-sm'
        }`}
      >
        <div className="h-32 bg-gray-100 flex items-center justify-center overflow-hidden">
          <DocTypeIcon doc={doc} />
        </div>
        <div className="p-3">
          <p className="text-xs font-medium text-gray-900 truncate">{doc.title || doc.fileName}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">{size} · {date}</p>
          {doc.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {doc.tags.slice(0, 2).map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-500">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </button>
    )
  }

  return (
    <button
      onClick={onSelect}
      aria-label={doc.title || doc.fileName}
      className={`w-full text-left flex items-center gap-3 p-3 rounded-xl border transition-all ${
        selected
          ? 'border-teal-500 bg-teal-50'
          : 'border-gray-200 hover:border-teal-300 hover:bg-gray-50'
      }`}
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden">
        <DocTypeIcon doc={doc} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{doc.title || doc.fileName}</p>
        <p className="text-xs text-gray-500">{doc.documentType} · {size} · {date}</p>
      </div>
      {doc.tags.slice(0, 1).map((tag) => (
        <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
          {tag}
        </span>
      ))}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function DocumentGrid({ patientId, selectedId, onSelect }: DocumentGridProps) {
  const { data: docs, isLoading, error } = usePatientDocuments(patientId)
  const [filter, setFilter] = useState('all')
  const [sortDesc, setSortDesc] = useState(true)
  const [gridView, setGridView] = useState(true)

  const filtered = useMemo(
    () =>
      (docs ?? [])
        .filter((d) => matchesFilter(d, filter))
        .sort((a, b) => {
          const diff = new Date(a.uploadedAt).getTime() - new Date(b.uploadedAt).getTime()
          return sortDesc ? -diff : diff
        }),
    [docs, filter, sortDesc]
  )

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-44 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12 text-sm text-red-400">
        Failed to load documents. Please try again.
      </div>
    )
  }

  return (
    <div>
      {/* Controls row */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 flex-wrap">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filter === tab.key ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setSortDesc((s) => !s)}
            aria-pressed={sortDesc}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border border-gray-200"
          >
            {sortDesc ? 'Newest first' : 'Oldest first'}
          </button>

          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setGridView(true)}
              aria-label="Grid view"
              className={`p-1.5 ${gridView ? 'bg-teal-50 text-teal-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setGridView(false)}
              aria-label="List view"
              className={`p-1.5 ${!gridView ? 'bg-teal-50 text-teal-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <List size={14} />
            </button>
          </div>
        </div>
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16">
          <FileText size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-sm text-gray-400">
            {filter === 'all' ? 'No documents uploaded yet.' : `No ${filter} documents found.`}
          </p>
        </div>
      )}

      {gridView ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {filtered.map((doc) => (
            <DocCard
              key={doc.id}
              doc={doc}
              selected={selectedId === doc.id}
              onSelect={() => onSelect(doc)}
              gridView
            />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((doc) => (
            <DocCard
              key={doc.id}
              doc={doc}
              selected={selectedId === doc.id}
              onSelect={() => onSelect(doc)}
              gridView={false}
            />
          ))}
        </div>
      )}
    </div>
  )
}
