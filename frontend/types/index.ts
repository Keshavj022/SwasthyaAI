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
