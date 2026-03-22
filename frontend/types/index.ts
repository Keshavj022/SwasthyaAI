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
  dateOfBirth: string
  bloodGroup: string
  allergies: string[]
  emergencyContact: string
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
  doctorId: string
  doctorName?: string
  dateTime: string
  status: 'scheduled' | 'completed' | 'cancelled' | 'pending' | 'confirmed'
  type: string
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
  attachmentUrl?: string  // runtime-only, not persisted to localStorage
}

export interface AgentResponse {
  response: string
  agentUsed: string
  confidence: number
  disclaimer: string
  reasoning?: string
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
  id: string           // normalized from document_id (integer → string)
  patientId: string
  fileName: string
  fileType: string     // mime type
  uploadedAt: string
  url: string          // download URL (constructed by frontend)
  title: string
  fileSize: number
  documentType: string
  tags: string[]
  description?: string
}

export interface AuditLog {
  id: string
  auditId: string
  timestamp: string
  userId: string
  agentType: string        // maps from agent_name
  confidenceScore: number | null
  explainabilityScore: number | null
  escalationTriggered: string | null
  reasoningSummary: string | null
  inputSummary: string
  outputSummary: string
  reviewed: boolean
  // legacy compat
  action?: string
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

export interface LabResultInput {
  testName: string
  value: number
  unit: string
  date?: string
}

export interface InterpretedResult {
  testName: string
  value: number
  unit: string
  status: 'normal' | 'low' | 'high' | 'critical'
  referenceRange: string
  explanation: string
  actionNeeded: boolean
}

export interface LabResultsResponse {
  results: InterpretedResult[]
  summary: string
  patternsDetected: string[]
  criticalFlags: string[]
  followUpTests: string[]
  disclaimer: string
}

export interface LabResultRecord {
  testName: string
  value: number
  unit: string
  date?: string
}

export interface SavedLabReport {
  id: string
  patientId: string
  reportDate: string
  labName: string
  testCount: number
  hasCritical: boolean
  createdAt: string
  results: LabResultRecord[]
}

export interface AdminUser {
  id: string
  email: string
  fullName: string
  role: 'doctor' | 'patient' | 'admin'
  isActive: boolean
  createdAt: string | null
}

export interface AdminStats {
  dbSizeKb: number
  totalPatients: number
  totalAuditLogs: number
  totalDocuments: number
  agentRequests: { agentName: string; count: number }[]
}

export interface AdminAppointment {
  id: string
  patientId: string
  doctorId: string | null
  doctorName: string | null
  specialty: string | null
  dateTime: string
  status: string
  type: string | null
  notes: string | null
}
