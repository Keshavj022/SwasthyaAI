// Shared TypeScript types for SwasthyaAI

export interface User {
  id: string
  name: string
  email: string
  role: 'doctor' | 'patient' | 'admin'
  createdAt: string
}

export interface Patient {
  id: string
  userId: string
  name?: string
  age?: number
  gender?: string
  dateOfBirth: string
  bloodGroup: string
  allergies: string[]
  emergencyContact: string
  activeConditions?: string[]
  currentMedications?: string[]
  lastCheckIn?: string
}

export interface Doctor {
  id: string
  userId: string
  specialty: string
  licenseNumber: string
  availableSlots: string[]
}

export interface Appointment {
  id: string
  patientId: string
  patientName?: string
  patientAge?: number
  doctorId: string
  doctorName?: string
  specialty?: string
  dateTime: string
  durationMinutes?: number
  status: 'scheduled' | 'completed' | 'cancelled' | 'pending' | 'confirmed'
  type: string
  reason?: string
  notes?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentType?: string
  timestamp: string
  confidence?: number
  disclaimer?: string
  reasoning?: string
}

export interface AgentResponse {
  response: string
  agentUsed: string
  confidence: number
  disclaimer: string
  reasoning?: string
  /** Full structured payload from the backend envelope (differential_diagnoses,
   *  red_flags, recommended_workup, findings, etc.) — preserved, not flattened. */
  data?: Record<string, unknown>
  emergency?: boolean
  auditId?: string
  intent?: Record<string, unknown> | null
  isStub?: boolean
}

export interface HealthCheckIn {
  id: string
  patientId: string
  mood: number
  energy: number
  sleep: number
  symptoms: string[]
  timestamp: string
}

export interface MedicalDocument {
  id: string
  patientId: string
  fileName: string
  fileType: string
  uploadedAt: string
  url: string
}

export interface AuditLog {
  id: string
  action: string
  agentType: string
  userId: string
  timestamp: string
  inputSummary: string
  outputSummary: string
}

export interface LabResult {
  id: string
  patientId: string
  testName: string
  value: string
  unit: string
  normalRange: string
  status: 'normal' | 'low' | 'high' | 'critical'
  timestamp: string
}

// --- Medications (patient dashboard reminders) ---
export interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  timeOfDay?: string
  taken?: boolean
}

// --- Lab Results Agent (Task 11) ---
export type LabResultStatus = 'normal' | 'low' | 'high' | 'critical'

export interface LabResultInput {
  test_name: string
  value: number
  unit: string
}

export interface InterpretedLabResult {
  test_name: string
  value: number
  unit: string
  status: LabResultStatus
  reference_range: string
  explanation: string
  action_needed: boolean
}

export interface LabResultsResponse {
  results: InterpretedLabResult[]
  summary: string
  patterns_detected: string[]
  critical_flags: string[]
  follow_up_tests: string[]
  disclaimer: string
}

export interface SavedLabResultSet {
  id: string
  patient_id: string
  report_date: string
  lab_name: string
  results: InterpretedLabResult[]
  critical_flags: string[]
}

// --- Admin panel (Task 10) ---
export interface AdminUser {
  id: string
  name: string
  email: string
  role: 'doctor' | 'patient' | 'admin'
  isActive: boolean
  createdAt: string
}

export interface SystemStats {
  totalUsers: number
  totalPatients: number
  totalDoctors: number
  totalAppointments: number
  totalDocuments: number
  totalAuditLogs: number
  aiQueriesToday?: number
}

// --- Documents / image viewer (Task 09) ---
export type DocumentType =
  | 'lab_report'
  | 'prescription'
  | 'imaging'
  | 'clinical_note'
  | 'discharge_summary'
  | 'other'

export interface AIModelStatus {
  name: string
  enabled: boolean
  loaded: boolean
  stub: boolean
  device?: string
  repoId?: string
}
