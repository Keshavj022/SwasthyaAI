/**
 * Centralized API service layer for the Hospital AI frontend.
 *
 * All agent interactions route through the orchestrator endpoint.
 * Designed for offline-first operation: every call returns a typed
 * result-or-error wrapper so the UI can degrade gracefully.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

/** Wraps every API call so callers never need try/catch. */
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; offline: boolean };

/** Common envelope returned by POST /api/orchestrator/query. */
export interface QueryResponse<TData = Record<string, unknown>> {
  success: boolean;
  agent: string | null;
  timestamp: string;
  confidence: { score: number; level: string } | null;
  data: TData;
  reasoning: string | null;
  disclaimer: string;
  audit_id: string | null;
  emergency: boolean | null;
  intent: Record<string, unknown> | null;
  safety_check: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Agent-specific data shapes
// ---------------------------------------------------------------------------

/** health_support / chat agent */
export interface ChatResponseData {
  response?: string;
  task?: string;
  alerts?: string[];
  recommendations?: string[];
  [key: string]: unknown;
}

/** diagnostic_support agent */
export interface DiagnosticDiagnosis {
  rank: number;
  condition: string;
  likelihood: string;
  confidence: number;
  supporting_features: string;
  contradicting_features: string;
  missing_information: string;
}

export interface DiagnosticResponseData {
  differential_diagnoses: DiagnosticDiagnosis[];
  red_flags: string[];
  recommended_workup: string[];
  clinical_correlation_needed: string[];
  most_likely_diagnosis: string;
  symptoms_analyzed: string[];
  emergency_detected: boolean;
  total_diagnoses_considered: number;
  disclaimer: string;
}

/** image_analysis agent */
export interface ImageFinding {
  finding: string;
  location: string;
  size?: string;
  severity: string;
  confidence: number;
  description: string;
  differential: string[];
}

export interface ImageRegion {
  region: string;
  coordinates: { x: number; y: number; width: number; height: number };
  description: string;
}

export interface ImageResponseData {
  modality: string;
  analysis_type: string;
  image_quality: string;
  findings: ImageFinding[];
  regions_of_interest: ImageRegion[];
  overall_impression: string;
  clinical_correlation: string[];
  recommended_next_steps: string[];
  limitations: string[];
  disclaimer: string;
}

/** voice agent */
export interface TranscriptionWord {
  word: string;
  confidence: number;
  start_time: number;
  end_time: number;
}

export interface TranscriptionResponseData {
  mode: string;
  language: string;
  transcription: string;
  confidence: number;
  audio_duration_seconds: number;
  words_detected: TranscriptionWord[];
  medical_terms_identified: string[];
  alternative_transcriptions: string[];
  next_action: string;
  disclaimer: string;
}

/** health_memory agent */
export interface PatientInfo {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  blood_type: string;
}

export interface HealthMemoryResponseData {
  patient_info: PatientInfo;
  active_prescriptions: {
    medication: string;
    dosage: string;
    frequency: string;
    prescribed_date: string;
  }[];
  active_diagnoses: {
    diagnosis_name: string;
    icd10_code: string;
    status: string;
    diagnosis_date: string;
  }[];
  allergies: {
    allergen: string;
    reaction: string;
    severity: string;
  }[];
  recent_visits: {
    visit_date: string;
    visit_type: string;
    chief_complaint: string;
    provider_name: string;
  }[];
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function isNetworkError(err: unknown): boolean {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) {
    return true;
  }
  if (err instanceof DOMException && err.name === "AbortError") {
    return true;
  }
  return false;
}

async function orchestratorQuery<TData>(
  message: string,
  userId: string,
  options?: {
    attachments?: string[];
    context?: Record<string, unknown>;
    timeoutMs?: number;
  }
): Promise<ApiResult<QueryResponse<TData>>> {
  const url = `${API_BASE_URL}/api/orchestrator/query`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        message,
        attachments: options?.attachments,
        context: options?.context,
      }),
      signal: AbortSignal.timeout(options?.timeoutMs ?? 30_000),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return {
        ok: false,
        error: `HTTP ${response.status}: ${text || response.statusText}`,
        offline: false,
      };
    }

    const data: QueryResponse<TData> = await response.json();
    return { ok: true, data };
  } catch (err) {
    const offline = isNetworkError(err);
    return {
      ok: false,
      error: offline
        ? "Cannot reach the backend. The system is operating offline."
        : err instanceof Error
          ? err.message
          : "Unknown error",
      offline,
    };
  }
}

// ---------------------------------------------------------------------------
// Public API methods
// ---------------------------------------------------------------------------

/**
 * Send a free-text chat message to the health support agent.
 *
 * The orchestrator routes the message based on intent — it may hit the
 * health_support, triage, or diagnostic agent depending on content.
 */
export async function sendChatMessage(
  message: string,
  userId: string,
  context?: Record<string, unknown>
): Promise<ApiResult<QueryResponse<ChatResponseData>>> {
  return orchestratorQuery<ChatResponseData>(message, userId, { context });
}

/**
 * Run a differential-diagnosis session.
 *
 * Provides structured symptom data so the orchestrator routes directly
 * to the diagnostic_support agent.
 */
export async function runDiagnostics(
  params: {
    symptoms: string[];
    duration?: string;
    severity?: string;
    vitalSigns?: {
      heart_rate?: number;
      blood_pressure_systolic?: number;
      blood_pressure_diastolic?: number;
      temperature?: number;
      respiratory_rate?: number;
      oxygen_saturation?: number;
    };
    patientContext?: {
      age?: number;
      gender?: string;
      conditions?: string[];
      medications?: string[];
    };
  },
  userId: string
): Promise<ApiResult<QueryResponse<DiagnosticResponseData>>> {
  const message = `Diagnose: ${params.symptoms.join(", ")}`;
  return orchestratorQuery<DiagnosticResponseData>(message, userId, {
    context: {
      task: "differential_diagnosis",
      symptoms: params.symptoms,
      duration: params.duration,
      severity: params.severity,
      vital_signs: params.vitalSigns,
      patient_context: params.patientContext,
    },
    timeoutMs: 60_000,
  });
}

/**
 * Upload a medical image for analysis.
 *
 * Reads the file into a base64 string and sends it as context so the
 * orchestrator routes to the image_analysis agent.
 */
export async function uploadImage(
  file: File,
  userId: string,
  options?: {
    modality?: string;
    clinicalContext?: string;
    analysisType?:
      | "finding_detection"
      | "abnormality_classification"
      | "region_description";
  }
): Promise<ApiResult<QueryResponse<ImageResponseData>>> {
  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1] ?? result);
    };
    reader.onerror = () => reject(new Error("Failed to read image file"));
    reader.readAsDataURL(file);
  });

  const message = options?.clinicalContext
    ? `Analyze this medical image: ${options.clinicalContext}`
    : "Analyze this medical image";

  return orchestratorQuery<ImageResponseData>(message, userId, {
    context: {
      image_data: base64,
      modality: options?.modality ?? "other",
      analysis_type: options?.analysisType ?? "finding_detection",
      clinical_context: options?.clinicalContext,
    },
    timeoutMs: 60_000,
  });
}

/**
 * Transcribe an audio recording via the voice agent.
 *
 * Reads the audio blob into base64 and sends it with the desired
 * transcription mode.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  userId: string,
  options?: {
    mode?:
      | "symptom_reporting"
      | "medical_dictation"
      | "voice_query"
      | "general";
    language?: string;
  }
): Promise<ApiResult<QueryResponse<TranscriptionResponseData>>> {
  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1] ?? result);
    };
    reader.onerror = () => reject(new Error("Failed to read audio data"));
    reader.readAsDataURL(audioBlob);
  });

  return orchestratorQuery<TranscriptionResponseData>(
    "Transcribe this audio",
    userId,
    {
      context: {
        audio_data: base64,
        mode: options?.mode ?? "general",
        language: options?.language ?? "en-US",
      },
      timeoutMs: 60_000,
    }
  );
}

/**
 * Fetch a patient's health memory / medical history summary.
 */
export async function fetchHealthMemory(
  patientId: string,
  userId: string,
  queryType:
    | "summary"
    | "timeline"
    | "medications"
    | "allergies"
    | "conditions" = "summary"
): Promise<ApiResult<QueryResponse<HealthMemoryResponseData>>> {
  return orchestratorQuery<HealthMemoryResponseData>(
    `Show patient medical ${queryType}`,
    userId,
    {
      context: {
        patient_id: patientId,
        query_type: queryType,
      },
    }
  );
}

// ---------------------------------------------------------------------------
// Utility endpoints (direct REST, not orchestrator)
// ---------------------------------------------------------------------------

/** Quick connectivity check against the backend health endpoint. */
export async function checkBackendHealth(): Promise<
  ApiResult<{
    status: string;
    application: string;
    version: string;
    timestamp: string;
  }>
> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      signal: AbortSignal.timeout(5_000),
    });

    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}`, offline: false };
    }

    return { ok: true, data: await response.json() };
  } catch (err) {
    return {
      ok: false,
      error: "Backend unreachable",
      offline: isNetworkError(err),
    };
  }
}

/** List all registered agents and their capabilities. */
export async function listAgents(): Promise<
  ApiResult<{
    total_agents: number;
    agents: {
      name: string;
      description: string;
      capabilities: string[];
      enabled: boolean;
      confidence_threshold: number;
    }[];
  }>
> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/orchestrator/agents`, {
      signal: AbortSignal.timeout(5_000),
    });

    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}`, offline: false };
    }

    return { ok: true, data: await response.json() };
  } catch (err) {
    return {
      ok: false,
      error: "Backend unreachable",
      offline: isNetworkError(err),
    };
  }
}

// ---------------------------------------------------------------------------
// Audit log types and API
// ---------------------------------------------------------------------------

export interface AuditLogEntry {
  audit_id: string;
  timestamp: string;
  agent_name: string;
  confidence_score: number | null;
  explainability_score: number | null;
  escalation_triggered: string | null;
  reasoning_summary: string | null;
  reviewed: boolean;
}

export interface AuditLogsResponse {
  total_results: number;
  filters_applied: {
    agent_name: string | null;
    min_confidence: number | null;
    escalations_only: boolean;
    hours: number;
  };
  logs: AuditLogEntry[];
}

/**
 * Fetch audit logs with optional filtering.
 */
export async function fetchAuditLogs(options?: {
  agent_name?: string;
  min_confidence?: number;
  escalations_only?: boolean;
  hours?: number;
  limit?: number;
}): Promise<ApiResult<AuditLogsResponse>> {
  const params = new URLSearchParams();
  if (options?.agent_name) params.append("agent_name", options.agent_name);
  if (options?.min_confidence !== undefined)
    params.append("min_confidence", options.min_confidence.toString());
  if (options?.escalations_only)
    params.append("escalations_only", "true");
  if (options?.hours) params.append("hours", options.hours.toString());
  if (options?.limit) params.append("limit", options.limit.toString());

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/audit/logs?${params.toString()}`,
      {
        signal: AbortSignal.timeout(10_000),
      }
    );

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return {
        ok: false,
        error: `HTTP ${response.status}: ${text || response.statusText}`,
        offline: false,
      };
    }

    return { ok: true, data: await response.json() };
  } catch (err) {
    const offline = isNetworkError(err);
    return {
      ok: false,
      error: offline
        ? "Cannot reach the backend. The system is operating offline."
        : err instanceof Error
          ? err.message
          : "Unknown error",
      offline,
    };
  }
}
