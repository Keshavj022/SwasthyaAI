/**
 * Centralized API service layer for SwasthyaAI.
 *
 * Typed Axios client with auth interceptors.
 * All agent interactions route through the orchestrator endpoint.
 */

import axios from 'axios'
import type {
  User,
  Patient,
  Appointment,
  Message,
  AgentResponse,
  HealthCheckIn,
  MedicalDocument,
  AuditLog,
  AdminUser,
  AdminStats,
  AdminAppointment,
  LabResultsResponse,
  LabResultInput,
  LabResultRecord,
  SavedLabReport,
} from '@/types'

// ---------------------------------------------------------------------------
// Additional payload / response types not in shared types
// ---------------------------------------------------------------------------

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  role: 'doctor' | 'patient' | 'admin'
}

/** Shape returned by the backend auth endpoints (snake_case) */
interface BackendUser {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
}

function normalizeUser(u: BackendUser): User {
  return {
    id: u.id,
    name: u.full_name,
    email: u.email,
    role: u.role as 'doctor' | 'patient' | 'admin',
    createdAt: u.created_at,
  }
}

export interface DoctorAvailability {
  doctorId: string
  doctorName: string
  specialty: string
  slots: string[]
}

export interface BookAppointmentPayload {
  patientId: string
  doctorId: string
  dateTime: string
  type: string
  notes?: string
}

export interface SystemHealth {
  status: string
  application: string
  version: string
  environment: string
  timestamp: string
  database: {
    status: string
    file_exists: boolean
    type: string
  }
  offline_mode: {
    enabled: boolean
    description: string
  }
}

// ---------------------------------------------------------------------------
// Re-export legacy types used by existing pages
// ---------------------------------------------------------------------------

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; offline: boolean }

export interface QueryResponse<TData = Record<string, unknown>> {
  success: boolean
  agent: string | null
  timestamp: string
  confidence: { score: number; level: string } | null
  data: TData
  reasoning: string | null
  disclaimer: string
  audit_id: string | null
  emergency: boolean | null
  intent: Record<string, unknown> | null
  safety_check: Record<string, unknown> | null
}

export interface ChatResponseData {
  response?: string
  task?: string
  alerts?: string[]
  recommendations?: string[]
  [key: string]: unknown
}

export interface DiagnosticDiagnosis {
  rank: number
  condition: string
  likelihood: string
  confidence: number
  supporting_features: string
  contradicting_features: string
  missing_information: string
}

export interface DiagnosticResponseData {
  differential_diagnoses: DiagnosticDiagnosis[]
  red_flags: string[]
  recommended_workup: string[]
  clinical_correlation_needed: string[]
  most_likely_diagnosis: string
  symptoms_analyzed: string[]
  emergency_detected: boolean
  total_diagnoses_considered: number
  disclaimer: string
}

export interface ImageFinding {
  finding: string
  location: string
  size?: string
  severity: string
  confidence: number
  description: string
  differential: string[]
}

export interface ImageRegion {
  region: string
  coordinates: { x: number; y: number; width: number; height: number }
  description: string
}

export interface ImageResponseData {
  modality: string
  analysis_type: string
  image_quality: string
  findings: ImageFinding[]
  regions_of_interest: ImageRegion[]
  overall_impression: string
  clinical_correlation: string[]
  recommended_next_steps: string[]
  limitations: string[]
  disclaimer: string
}

export interface TranscriptionWord {
  word: string
  confidence: number
  start_time: number
  end_time: number
}

export interface TranscriptionResponseData {
  mode: string
  language: string
  transcription: string
  confidence: number
  audio_duration_seconds: number
  words_detected: TranscriptionWord[]
  medical_terms_identified: string[]
  alternative_transcriptions: string[]
  next_action: string
  disclaimer: string
}

export interface PatientInfo {
  patient_id: string
  name: string
  age: number
  gender: string
  blood_type: string
}

export interface HealthMemoryResponseData {
  patient_info: PatientInfo
  active_prescriptions: {
    medication: string
    dosage: string
    frequency: string
    prescribed_date: string
  }[]
  active_diagnoses: {
    diagnosis_name: string
    icd10_code: string
    status: string
    diagnosis_date: string
  }[]
  allergies: {
    allergen: string
    reaction: string
    severity: string
  }[]
  recent_visits: {
    visit_date: string
    visit_type: string
    chief_complaint: string
    provider_name: string
  }[]
  [key: string]: unknown
}

export interface AuditLogEntry {
  audit_id: string
  timestamp: string
  agent_name: string
  confidence_score: number | null
  explainability_score: number | null
  escalation_triggered: string | null
  reasoning_summary: string | null
  reviewed: boolean
}

export interface AuditLogsResponse {
  total_results: number
  filters_applied: {
    agent_name: string | null
    min_confidence: number | null
    escalations_only: boolean
    hours: number
  }
  logs: AuditLogEntry[]
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const TOKEN_KEY = 'swasthya_token'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

// Request interceptor: attach Bearer token
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Response interceptor: on 401 clear token and redirect
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const authApi = {
  login: async (email: string, password: string, _role?: string): Promise<{ token: string; user: User }> => {
    const { data } = await apiClient.post('/api/auth/login', { email, password })
    return { token: data.access_token, user: normalizeUser(data.user) }
  },

  register: async (payload: RegisterPayload): Promise<{ token: string; user: User }> => {
    const { data } = await apiClient.post('/api/auth/register', payload)
    return { token: data.access_token, user: normalizeUser(data.user) }
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/auth/me')
    return normalizeUser(data)
  },

  logout: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY)
    }
  },
}

// ---------------------------------------------------------------------------
// Orchestrator / Chat API
// ---------------------------------------------------------------------------

export const orchestratorApi = {
  ask: async (
    query: string,
    patientId?: string,
    context?: Record<string, unknown>
  ): Promise<AgentResponse> => {
    const { data } = await apiClient.post('/api/orchestrator/query', {
      message: query,
      patient_id: patientId,
      context,
    })
    // Normalise backend envelope → AgentResponse
    return {
      response: data.data?.response ?? data.data?.task ?? '',
      agentUsed: data.agent ?? 'unknown',
      confidence: data.confidence?.score ?? 0,
      disclaimer: data.disclaimer ?? '',
      reasoning: data.reasoning ?? undefined,
    }
  },
}

// ---------------------------------------------------------------------------
// Patient API
// ---------------------------------------------------------------------------

export const patientApi = {
  getAll: async (): Promise<Patient[]> => {
    const { data } = await apiClient.get('/api/patients')
    return data
  },

  getById: async (id: string): Promise<Patient> => {
    const { data } = await apiClient.get(`/api/patients/${id}`)
    return data
  },

  create: async (payload: Partial<Patient>): Promise<Patient> => {
    const { data } = await apiClient.post('/api/patients', payload)
    return data
  },

  update: async (id: string, payload: Partial<Patient>): Promise<Patient> => {
    const { data } = await apiClient.put(`/api/patients/${id}`, payload)
    return data
  },

  getHealthHistory: async (patientId: string): Promise<HealthCheckIn[]> => {
    const { data } = await apiClient.get(`/api/patients/${patientId}/health-history`)
    return data
  },

  submitCheckIn: async (patientId: string, payload: Partial<HealthCheckIn>): Promise<HealthCheckIn> => {
    const { data } = await apiClient.post(`/api/patients/${patientId}/check-in`, payload)
    return data
  },
}

// ---------------------------------------------------------------------------
// Appointment API
// ---------------------------------------------------------------------------

export const appointmentApi = {
  getAvailability: async (specialty?: string, doctorName?: string): Promise<DoctorAvailability[]> => {
    const params = new URLSearchParams()
    if (specialty) params.append('specialty', specialty)
    if (doctorName) params.append('doctor_name', doctorName)
    const { data } = await apiClient.get(`/api/appointments/availability?${params}`)
    return data
  },

  book: async (payload: BookAppointmentPayload): Promise<Appointment> => {
    const { data } = await apiClient.post('/api/appointments', payload)
    return data
  },

  getByPatient: async (patientId: string): Promise<Appointment[]> => {
    const { data } = await apiClient.get(`/api/appointments?patient_id=${patientId}`)
    return data
  },

  reschedule: async (appointmentId: string, newDateTime: string): Promise<Appointment> => {
    const { data } = await apiClient.patch(`/api/appointments/${appointmentId}`, { dateTime: newDateTime })
    return data
  },

  cancel: async (appointmentId: string): Promise<{ success: boolean }> => {
    const { data } = await apiClient.delete(`/api/appointments/${appointmentId}`)
    return data
  },
}

// ---------------------------------------------------------------------------
// Document API
// ---------------------------------------------------------------------------

interface BackendDocument {
  document_id: number
  title: string
  document_type: string
  file_name: string
  file_size: number
  mime_type: string
  document_date: string | null
  uploaded_at: string
  tags: string[] | null
  visit_id: number | null
  description?: string
}

function normalizeDocument(raw: BackendDocument, patientId: string): MedicalDocument {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
  return {
    id: String(raw.document_id),
    patientId,
    fileName: raw.file_name,
    fileType: raw.mime_type,
    uploadedAt: raw.uploaded_at ?? new Date().toISOString(),
    url: `${base}/api/documents/${raw.document_id}/download`,
    title: raw.title,
    fileSize: raw.file_size,
    documentType: raw.document_type,
    tags: raw.tags ?? [],
    description: raw.description,
  }
}

export interface UploadDocumentPayload {
  patientId: string
  file: File
  documentType: string
  title: string
  description?: string
  tags?: string[]
}

export const documentApi = {
  upload: async (payload: UploadDocumentPayload): Promise<MedicalDocument> => {
    const form = new FormData()
    form.append('file', payload.file)
    form.append('patient_id', payload.patientId)
    form.append('document_type', payload.documentType)
    form.append('title', payload.title)
    if (payload.description) form.append('description', payload.description)
    if (payload.tags?.length) form.append('tags', payload.tags.join(','))
    const { data } = await apiClient.post('/api/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return normalizeDocument(
      {
        document_id: data.document_id,
        title: data.title,
        document_type: data.document_type,
        file_name: data.file_name,
        file_size: data.file_size,
        mime_type: data.mime_type,
        document_date: null,
        uploaded_at: data.uploaded_at,
        tags: data.tags ?? payload.tags ?? null,
        visit_id: null,
      },
      payload.patientId
    )
  },

  getByPatient: async (patientId: string): Promise<MedicalDocument[]> => {
    const { data } = await apiClient.get(`/api/documents/patient/${patientId}`)
    const docs: BackendDocument[] = data.documents ?? []
    return docs.map((d) => normalizeDocument(d, patientId))
  },

  delete: async (documentId: string): Promise<{ success: boolean }> => {
    const { data } = await apiClient.delete(`/api/documents/${documentId}`)
    return data
  },

  getUrl: (documentId: string): string => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
    return `${base}/api/documents/${documentId}/download`
  },
}

// ---------------------------------------------------------------------------
// Audit API — raw types & normalizers
// ---------------------------------------------------------------------------

interface RawAuditLog {
  id?: string | number
  audit_id: string
  timestamp: string
  user_id?: string
  agent_name?: string
  confidence_score?: number | null
  explainability_score?: number | null
  escalation_triggered?: string | null
  reasoning_summary?: string | null
  input_summary?: string
  output_summary?: string
  reviewed?: boolean
}

function normalizeAuditLog(raw: RawAuditLog): AuditLog {
  return {
    id: String(raw.id ?? raw.audit_id),
    auditId: raw.audit_id,
    timestamp: raw.timestamp,
    userId: raw.user_id ?? '',
    agentType: raw.agent_name ?? '',
    confidenceScore: raw.confidence_score ?? null,
    explainabilityScore: raw.explainability_score ?? null,
    escalationTriggered: raw.escalation_triggered ?? null,
    reasoningSummary: raw.reasoning_summary ?? null,
    inputSummary: raw.input_summary ?? '',
    outputSummary: raw.output_summary ?? '',
    reviewed: Boolean(raw.reviewed),
  }
}

// ---------------------------------------------------------------------------
// Audit API
// ---------------------------------------------------------------------------

export const auditApi = {
  getLogs: async (params?: {
    limit?: number
    offset?: number
    agentType?: string
    userId?: string
    minConfidence?: number
    escalationsOnly?: boolean
    fromDate?: string
    toDate?: string
    hours?: number
  }): Promise<{ logs: AuditLog[]; total: number }> => {
    const qs = new URLSearchParams()
    if (params?.limit !== undefined) qs.append('limit', String(params.limit))
    if (params?.offset !== undefined) qs.append('offset', String(params.offset))
    if (params?.agentType) qs.append('agent_name', params.agentType)
    if (params?.userId) qs.append('user_id', params.userId)
    if (params?.minConfidence !== undefined) qs.append('min_confidence', String(params.minConfidence))
    if (params?.escalationsOnly) qs.append('escalations_only', 'true')
    if (params?.fromDate) qs.append('from_date', params.fromDate)
    if (params?.toDate) qs.append('to_date', params.toDate)
    if (params?.hours !== undefined) qs.append('hours', String(params.hours))
    const { data } = await apiClient.get(`/api/audit/logs?${qs}`)
    const rawLogs: RawAuditLog[] = data.logs ?? data
    return {
      logs: rawLogs.map(normalizeAuditLog),
      total: data.total_results ?? data.total ?? rawLogs.length,
    }
  },
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

interface RawAdminUser {
  id: string | number
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string | null
}

interface RawAdminAppointment {
  id: string | number
  patient_id: string | number
  doctor_id: string | number | null
  doctor_name: string | null
  specialty: string | null
  date_time: string
  status: string
  type: string | null
  notes: string | null
}

function normalizeAdminUser(raw: RawAdminUser): AdminUser {
  return {
    id: String(raw.id),
    email: raw.email,
    fullName: raw.full_name,
    role: raw.role as AdminUser['role'],
    isActive: Boolean(raw.is_active),
    createdAt: raw.created_at ?? null,
  }
}

export const adminApi = {
  listUsers: async (): Promise<AdminUser[]> => {
    const { data } = await apiClient.get('/api/admin/users')
    return (data as RawAdminUser[]).map(normalizeAdminUser)
  },

  createUser: async (payload: {
    email: string
    password: string
    fullName: string
    role: string
  }): Promise<AdminUser> => {
    const { data } = await apiClient.post('/api/admin/users', {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
      role: payload.role,
    })
    return normalizeAdminUser(data)
  },

  updateUser: async (userId: string, patch: { role?: string; isActive?: boolean }): Promise<AdminUser> => {
    const body: Record<string, unknown> = {}
    if (patch.role !== undefined) body.role = patch.role
    if (patch.isActive !== undefined) body.is_active = patch.isActive
    const { data } = await apiClient.patch(`/api/admin/users/${userId}`, body)
    return normalizeAdminUser(data)
  },

  resetPassword: async (userId: string): Promise<{ tempPassword: string }> => {
    const { data } = await apiClient.post(`/api/admin/users/${userId}/reset-password`)
    return { tempPassword: data.temp_password }
  },

  deleteUser: async (userId: string): Promise<void> => {
    await apiClient.delete(`/api/admin/users/${userId}`)
  },

  getStats: async (): Promise<AdminStats> => {
    const { data } = await apiClient.get('/api/admin/stats')
    return {
      dbSizeKb: data.db_size_kb,
      totalPatients: data.total_patients,
      totalAuditLogs: data.total_audit_logs,
      totalDocuments: data.total_documents,
      agentRequests: (data.agent_requests ?? []).map((r: { agent_name: string; count: number }) => ({
        agentName: r.agent_name,
        count: r.count,
      })),
    }
  },

  listAppointments: async (params?: {
    status?: string
    specialty?: string
    fromDate?: string
    toDate?: string
    limit?: number
    offset?: number
  }): Promise<{ total: number; appointments: AdminAppointment[] }> => {
    const qs = new URLSearchParams()
    if (params?.status) qs.append('status', params.status)
    if (params?.specialty) qs.append('specialty', params.specialty)
    if (params?.fromDate) qs.append('from_date', params.fromDate)
    if (params?.toDate) qs.append('to_date', params.toDate)
    if (params?.limit !== undefined) qs.append('limit', String(params.limit))
    if (params?.offset !== undefined) qs.append('offset', String(params.offset))
    const { data } = await apiClient.get(`/api/admin/appointments?${qs}`)
    return {
      total: data.total ?? 0,
      appointments: (data.appointments ?? []).map((a: RawAdminAppointment) => ({
        id: String(a.id),
        patientId: String(a.patient_id),
        doctorId: a.doctor_id ? String(a.doctor_id) : null,
        doctorName: a.doctor_name ?? null,
        specialty: a.specialty ?? null,
        dateTime: a.date_time,
        status: a.status,
        type: a.type ?? null,
        notes: a.notes ?? null,
      })),
    }
  },
}

// ---------------------------------------------------------------------------
// Health API
// ---------------------------------------------------------------------------

export const healthApi = {
  check: async (): Promise<SystemHealth> => {
    const { data } = await apiClient.get('/api/health')
    return data
  },

  ping: async (): Promise<{ status: string }> => {
    const { data } = await apiClient.get('/api/health/ping')
    return data
  },
}

// ---------------------------------------------------------------------------
// Lab Results API
// ---------------------------------------------------------------------------

interface RawInterpretedResult {
  test_name: string
  value: number
  unit: string
  status: 'normal' | 'low' | 'high' | 'critical'
  reference_range: string
  explanation: string
  action_needed: boolean
}

interface RawLabResultsResponse {
  results: RawInterpretedResult[]
  summary: string
  patterns_detected: string[]
  critical_flags: string[]
  follow_up_tests: string[]
  disclaimer: string
}

interface RawSavedLabReport {
  id: string
  patient_id: string
  report_date: string
  lab_name: string
  test_count: number
  has_critical: boolean
  created_at: string
  results: { test_name: string; value: number; unit: string; date?: string }[]
}

function normalizeLabResultsResponse(raw: RawLabResultsResponse): LabResultsResponse {
  return {
    results: raw.results.map((r) => ({
      testName: r.test_name,
      value: r.value,
      unit: r.unit,
      status: r.status,
      referenceRange: r.reference_range,
      explanation: r.explanation,
      actionNeeded: r.action_needed,
    })),
    summary: raw.summary,
    patternsDetected: raw.patterns_detected,
    criticalFlags: raw.critical_flags,
    followUpTests: raw.follow_up_tests,
    disclaimer: raw.disclaimer,
  }
}

function normalizeSavedLabReport(raw: RawSavedLabReport): SavedLabReport {
  return {
    id: raw.id,
    patientId: raw.patient_id,
    reportDate: raw.report_date,
    labName: raw.lab_name,
    testCount: raw.test_count,
    hasCritical: raw.has_critical,
    createdAt: raw.created_at,
    results: (raw.results ?? []).map((r) => ({
      testName: r.test_name,
      value: r.value,
      unit: r.unit,
      date: r.date,
    })),
  }
}

export const labResultsApi = {
  interpret: async (params: {
    results: LabResultInput[]
    patientId: string
    patientAge: number
    patientSex: 'male' | 'female' | 'other'
  }): Promise<LabResultsResponse> => {
    const { data } = await apiClient.post('/api/lab-results/interpret', {
      results: params.results.map((r) => ({
        test_name: r.testName,
        value: r.value,
        unit: r.unit,
        date: r.date,
      })),
      patient_id: params.patientId,
      patient_age: params.patientAge,
      patient_sex: params.patientSex,
    })
    return normalizeLabResultsResponse(data as RawLabResultsResponse)
  },

  save: async (params: {
    patientId: string
    results: LabResultInput[]
    reportDate: string
    labName: string
    patientAge: number
    patientSex: 'male' | 'female' | 'other'
  }): Promise<{ id: string; saved: boolean }> => {
    const { data } = await apiClient.post('/api/lab-results/save', {
      patient_id: params.patientId,
      results: params.results.map((r) => ({
        test_name: r.testName,
        value: r.value,
        unit: r.unit,
        date: r.date,
      })),
      report_date: params.reportDate,
      lab_name: params.labName,
      patient_age: params.patientAge,
      patient_sex: params.patientSex,
    })
    return data
  },

  getHistory: async (patientId: string): Promise<SavedLabReport[]> => {
    const { data } = await apiClient.get(`/api/lab-results/${patientId}`)
    return (data as RawSavedLabReport[]).map(normalizeSavedLabReport)
  },
}

// ---------------------------------------------------------------------------
// Legacy fetch-based helpers (kept for backward-compat with existing pages)
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

function isNetworkError(err: unknown): boolean {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) return true
  if (err instanceof DOMException && err.name === 'AbortError') return true
  return false
}

async function orchestratorQuery<TData>(
  message: string,
  userId: string,
  options?: { attachments?: string[]; context?: Record<string, unknown>; timeoutMs?: number }
): Promise<ApiResult<QueryResponse<TData>>> {
  const url = `${API_BASE_URL}/api/orchestrator/query`
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, message, attachments: options?.attachments, context: options?.context }),
      signal: AbortSignal.timeout(options?.timeoutMs ?? 30_000),
    })
    if (!response.ok) {
      const text = await response.text().catch(() => '')
      return { ok: false, error: `HTTP ${response.status}: ${text || response.statusText}`, offline: false }
    }
    return { ok: true, data: await response.json() }
  } catch (err) {
    const offline = isNetworkError(err)
    return {
      ok: false,
      error: offline
        ? 'Cannot reach the backend. The system is operating offline.'
        : err instanceof Error
          ? err.message
          : 'Unknown error',
      offline,
    }
  }
}

export async function sendChatMessage(
  message: string,
  userId: string,
  context?: Record<string, unknown>
): Promise<ApiResult<QueryResponse<ChatResponseData>>> {
  return orchestratorQuery<ChatResponseData>(message, userId, { context })
}

export async function runDiagnostics(
  params: {
    symptoms: string[]
    duration?: string
    severity?: string
    vitalSigns?: {
      heart_rate?: number
      blood_pressure_systolic?: number
      blood_pressure_diastolic?: number
      temperature?: number
      respiratory_rate?: number
      oxygen_saturation?: number
    }
    patientContext?: { age?: number; gender?: string; conditions?: string[]; medications?: string[] }
  },
  userId: string
): Promise<ApiResult<QueryResponse<DiagnosticResponseData>>> {
  const message = `Diagnose: ${params.symptoms.join(', ')}`
  return orchestratorQuery<DiagnosticResponseData>(message, userId, {
    context: {
      task: 'differential_diagnosis',
      symptoms: params.symptoms,
      duration: params.duration,
      severity: params.severity,
      vital_signs: params.vitalSigns,
      patient_context: params.patientContext,
    },
    timeoutMs: 60_000,
  })
}

export async function uploadImage(
  file: File,
  userId: string,
  options?: {
    modality?: string
    clinicalContext?: string
    analysisType?: 'finding_detection' | 'abnormality_classification' | 'region_description'
  }
): Promise<ApiResult<QueryResponse<ImageResponseData>>> {
  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => { const r = reader.result as string; resolve(r.split(',')[1] ?? r) }
    reader.onerror = () => reject(new Error('Failed to read image file'))
    reader.readAsDataURL(file)
  })
  const message = options?.clinicalContext
    ? `Analyze this medical image: ${options.clinicalContext}`
    : 'Analyze this medical image'
  return orchestratorQuery<ImageResponseData>(message, userId, {
    context: { image_data: base64, modality: options?.modality ?? 'other', analysis_type: options?.analysisType ?? 'finding_detection', clinical_context: options?.clinicalContext },
    timeoutMs: 60_000,
  })
}

export async function transcribeAudio(
  audioBlob: Blob,
  userId: string,
  options?: { mode?: 'symptom_reporting' | 'medical_dictation' | 'voice_query' | 'general'; language?: string }
): Promise<ApiResult<QueryResponse<TranscriptionResponseData>>> {
  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => { const r = reader.result as string; resolve(r.split(',')[1] ?? r) }
    reader.onerror = () => reject(new Error('Failed to read audio data'))
    reader.readAsDataURL(audioBlob)
  })
  return orchestratorQuery<TranscriptionResponseData>('Transcribe this audio', userId, {
    context: { audio_data: base64, mode: options?.mode ?? 'general', language: options?.language ?? 'en-US' },
    timeoutMs: 60_000,
  })
}

export async function fetchHealthMemory(
  patientId: string,
  userId: string,
  queryType: 'summary' | 'timeline' | 'medications' | 'allergies' | 'conditions' = 'summary'
): Promise<ApiResult<QueryResponse<HealthMemoryResponseData>>> {
  return orchestratorQuery<HealthMemoryResponseData>(`Show patient medical ${queryType}`, userId, {
    context: { patient_id: patientId, query_type: queryType },
  })
}

export async function checkBackendHealth(): Promise<ApiResult<{ status: string; application: string; version: string; timestamp: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, { signal: AbortSignal.timeout(5_000) })
    if (!response.ok) return { ok: false, error: `HTTP ${response.status}`, offline: false }
    return { ok: true, data: await response.json() }
  } catch (err) {
    return { ok: false, error: 'Backend unreachable', offline: isNetworkError(err) }
  }
}

export async function listAgents(): Promise<ApiResult<{ total_agents: number; agents: { name: string; description: string; capabilities: string[]; enabled: boolean; confidence_threshold: number }[] }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/orchestrator/agents`, { signal: AbortSignal.timeout(5_000) })
    if (!response.ok) return { ok: false, error: `HTTP ${response.status}`, offline: false }
    return { ok: true, data: await response.json() }
  } catch (err) {
    return { ok: false, error: 'Backend unreachable', offline: isNetworkError(err) }
  }
}

/**
 * @deprecated Use `auditApi.getLogs` and `useAuditLogs` hook instead.
 * This function returns unnormalized AuditLogEntry objects (snake_case, no auditId etc.)
 * and will not be updated with new filter params.
 */
export async function fetchAuditLogs(options?: {
  agent_name?: string
  min_confidence?: number
  escalations_only?: boolean
  hours?: number
  limit?: number
}): Promise<ApiResult<AuditLogsResponse>> {
  const params = new URLSearchParams()
  if (options?.agent_name) params.append('agent_name', options.agent_name)
  if (options?.min_confidence !== undefined) params.append('min_confidence', options.min_confidence.toString())
  if (options?.escalations_only) params.append('escalations_only', 'true')
  if (options?.hours) params.append('hours', options.hours.toString())
  if (options?.limit) params.append('limit', options.limit.toString())
  try {
    const response = await fetch(`${API_BASE_URL}/api/audit/logs?${params.toString()}`, { signal: AbortSignal.timeout(10_000) })
    if (!response.ok) {
      const text = await response.text().catch(() => '')
      return { ok: false, error: `HTTP ${response.status}: ${text || response.statusText}`, offline: false }
    }
    return { ok: true, data: await response.json() }
  } catch (err) {
    const offline = isNetworkError(err)
    return { ok: false, error: offline ? 'Cannot reach the backend. The system is operating offline.' : err instanceof Error ? err.message : 'Unknown error', offline }
  }
}
