"use client";

import { useCallback, useEffect, useState } from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import { fetchHealthMemory } from "@/lib/api";
import type {
  HealthMemoryResponseData,
  QueryResponse,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TimelineItem =
  | {
      type: "prescription";
      date: string;
      data: HealthMemoryResponseData["active_prescriptions"][number];
    }
  | {
      type: "report";
      date: string;
      data: HealthMemoryResponseData["active_diagnoses"][number];
    }
  | {
      type: "appointment";
      date: string;
      data: HealthMemoryResponseData["recent_visits"][number];
    };

type PageState =
  | { kind: "loading" }
  | {
      kind: "loaded";
      data: QueryResponse<HealthMemoryResponseData>;
      timeline: TimelineItem[];
    }
  | { kind: "error"; message: string; offline: boolean };

const USER_ID = "patient_local";
const DEFAULT_PATIENT_ID = "demo_patient_001";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}

function formatDateShort(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
}

function buildTimeline(
  data: HealthMemoryResponseData
): TimelineItem[] {
  const items: TimelineItem[] = [];

  // Add prescriptions (with null check)
  if (data.active_prescriptions && Array.isArray(data.active_prescriptions)) {
    data.active_prescriptions.forEach((prescription) => {
      items.push({
        type: "prescription",
        date: prescription.prescribed_date,
        data: prescription,
      });
    });
  }

  // Add diagnoses (reports) (with null check)
  if (data.active_diagnoses && Array.isArray(data.active_diagnoses)) {
    data.active_diagnoses.forEach((diagnosis) => {
      items.push({
        type: "report",
        date: diagnosis.diagnosis_date,
        data: diagnosis,
      });
    });
  }

  // Add visits (appointments) (with null check)
  if (data.recent_visits && Array.isArray(data.recent_visits)) {
    data.recent_visits.forEach((visit) => {
      items.push({
        type: "appointment",
        date: visit.visit_date,
        data: visit,
      });
    });
  }

  // Sort by date (most recent first)
  return items.sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateB - dateA;
  });
}

function getItemIcon(type: TimelineItem["type"]): string {
  switch (type) {
    case "prescription":
      return "💊";
    case "report":
      return "📋";
    case "appointment":
      return "📅";
  }
}

function getItemLabel(type: TimelineItem["type"]): string {
  switch (type) {
    case "prescription":
      return "Prescription";
    case "report":
      return "Diagnosis Report";
    case "appointment":
      return "Appointment";
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PrescriptionCard({
  prescription,
  date,
}: {
  prescription: HealthMemoryResponseData["active_prescriptions"][number];
  date: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="shrink-0 w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center text-xl">
        💊
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-1">
          <h4 className="text-sm font-semibold text-gray-900">
            {prescription.medication}
          </h4>
          <time
            className="text-xs text-gray-500 shrink-0"
            dateTime={date}
          >
            {formatDate(date)}
          </time>
        </div>
        <div className="text-xs text-gray-600 space-y-0.5">
          <p>
            <span className="font-medium">Dosage:</span> {prescription.dosage}
          </p>
          <p>
            <span className="font-medium">Frequency:</span> {prescription.frequency}
          </p>
        </div>
      </div>
    </div>
  );
}

function ReportCard({
  diagnosis,
  date,
}: {
  diagnosis: HealthMemoryResponseData["active_diagnoses"][number];
  date: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="shrink-0 w-12 h-12 rounded-lg bg-purple-50 flex items-center justify-center text-xl">
        📋
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-1">
          <h4 className="text-sm font-semibold text-gray-900">
            {diagnosis.diagnosis_name}
          </h4>
          <time
            className="text-xs text-gray-500 shrink-0"
            dateTime={date}
          >
            {formatDate(date)}
          </time>
        </div>
        <div className="text-xs text-gray-600 space-y-0.5">
          <p>
            <span className="font-medium">ICD-10:</span> {diagnosis.icd10_code}
          </p>
          <p>
            <span className="font-medium">Status:</span>{" "}
            <span className="capitalize">{diagnosis.status}</span>
          </p>
        </div>
      </div>
    </div>
  );
}

function AppointmentCard({
  visit,
  date,
}: {
  visit: HealthMemoryResponseData["recent_visits"][number];
  date: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="shrink-0 w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center text-xl">
        📅
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-1">
          <h4 className="text-sm font-semibold text-gray-900">
            {visit.visit_type}
          </h4>
          <time
            className="text-xs text-gray-500 shrink-0"
            dateTime={date}
          >
            {formatDate(date)}
          </time>
        </div>
        <div className="text-xs text-gray-600 space-y-0.5">
          {visit.chief_complaint && (
            <p>
              <span className="font-medium">Chief Complaint:</span>{" "}
              {visit.chief_complaint}
            </p>
          )}
          {visit.provider_name && (
            <p>
              <span className="font-medium">Provider:</span> {visit.provider_name}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function TimelineItemCard({ item }: { item: TimelineItem }) {
  return (
    <div className="border-l-2 border-gray-200 pl-4 pb-4 last:pb-0 relative">
      {/* Timeline dot */}
      <div className="absolute left-0 top-2 -translate-x-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-400 z-10" />
      
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        {item.type === "prescription" && (
          <PrescriptionCard prescription={item.data} date={item.date} />
        )}
        {item.type === "report" && (
          <ReportCard diagnosis={item.data} date={item.date} />
        )}
        {item.type === "appointment" && (
          <AppointmentCard visit={item.data} date={item.date} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function MemoryPage() {
  const [state, setState] = useState<PageState>({ kind: "loading" });
  const [patientId, setPatientId] = useState(DEFAULT_PATIENT_ID);
  const [isOnline, setIsOnline] = useState(true);

  // ── Online / offline detection ───────────────────────────────────────────
  useEffect(() => {
    const update = () => setIsOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    update();
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  // ── Load patient data ────────────────────────────────────────────────────
  const loadPatientData = useCallback(async () => {
    setState({ kind: "loading" });

    const result = await fetchHealthMemory(patientId, USER_ID, "summary");

    if (result.ok) {
      const timeline = buildTimeline(result.data.data);
      setState({ kind: "loaded", data: result.data, timeline });
    } else {
      setState({
        kind: "error",
        message: result.error,
        offline: result.offline,
      });
    }
  }, [patientId]);

  useEffect(() => {
    loadPatientData();
  }, [loadPatientData]);

  // ── Group timeline by date ────────────────────────────────────────────────
  const groupedTimeline = state.kind === "loaded" ? (() => {
    const groups: Record<string, TimelineItem[]> = {};
    state.timeline.forEach((item) => {
      const dateKey = formatDateShort(item.date);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(item);
    });
    return groups;
  })() : {};

  return (
    <PageContainer
      title="Health Memory"
      description="Patient medical history timeline. Read-only view of prescriptions, diagnoses, and appointments."
      icon="🧠"
    >
      {/* Offline banner */}
      {!isOnline && (
        <SafetyBanner
          level="warning"
          title="You are offline"
          description="Patient data cannot be loaded while offline."
        />
      )}

      {/* Error banner */}
      {state.kind === "error" && (
        <SafetyBanner
          level="warning"
          title={
            state.offline
              ? "Offline — data unavailable"
              : "Unable to load patient data"
          }
          description={state.message}
        />
      )}

      {/* Patient selector */}
      {state.kind !== "loading" && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <label
            htmlFor="patient-select"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Patient ID
          </label>
          <input
            id="patient-select"
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            onBlur={loadPatientData}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                loadPatientData();
              }
            }}
            placeholder="Enter patient ID"
            className="w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>
      )}

      {/* Loading state */}
      {state.kind === "loading" && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 shadow-sm text-center">
          <div className="w-12 h-12 mx-auto mb-4">
            <svg
              className="w-12 h-12 text-blue-600 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-600">Loading patient data...</p>
        </div>
      )}

      {/* Patient info header */}
      {state.kind === "loaded" && state.data.data.patient_info && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {state.data.data.patient_info.name || "Unknown Patient"}
              </h2>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
                {state.data.data.patient_info.age !== undefined && (
                  <span>
                    <span className="font-medium">Age:</span> {state.data.data.patient_info.age}
                  </span>
                )}
                {state.data.data.patient_info.gender && (
                  <span>
                    <span className="font-medium">Gender:</span>{" "}
                    {state.data.data.patient_info.gender}
                  </span>
                )}
                {state.data.data.patient_info.blood_type && (
                  <span>
                    <span className="font-medium">Blood Type:</span>{" "}
                    {state.data.data.patient_info.blood_type}
                  </span>
                )}
              </div>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p>Patient ID: {state.data.data.patient_info.patient_id || patientId}</p>
            </div>
          </div>
        </div>
      )}

      {/* Summary stats */}
      {state.kind === "loaded" && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Active Prescriptions</p>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {state.data.data.active_prescriptions?.length ?? 0}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Active Diagnoses</p>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {state.data.data.active_diagnoses?.length ?? 0}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Recent Visits</p>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {state.data.data.recent_visits?.length ?? 0}
            </p>
          </div>
        </div>
      )}

      {/* Allergies section */}
      {state.kind === "loaded" &&
        state.data.data.allergies &&
        Array.isArray(state.data.data.allergies) &&
        state.data.data.allergies.length > 0 && (
          <div className="bg-red-50 rounded-lg border border-red-200 p-4">
            <h3 className="text-sm font-semibold text-red-900 mb-2">
              Known Allergies
            </h3>
            <div className="space-y-1">
              {state.data.data.allergies.map((allergy, i) => (
                <div key={i} className="text-sm text-red-800">
                  <span className="font-medium">{allergy.allergen}</span>
                  {allergy.reaction && (
                    <span className="text-red-700">
                      {" "}
                      — {allergy.reaction}
                      {allergy.severity && ` (${allergy.severity})`}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Timeline */}
      {state.kind === "loaded" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              Medical Timeline
            </h2>
            <p className="text-xs text-gray-500">
              {state.timeline.length} total entries
            </p>
          </div>

          {state.timeline.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 shadow-sm text-center">
              <p className="text-sm text-gray-500">
                No medical history entries found for this patient.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="space-y-6">
                {Object.entries(groupedTimeline)
                  .sort(([dateA], [dateB]) => {
                    return new Date(dateB).getTime() - new Date(dateA).getTime();
                  })
                  .map(([dateKey, items]) => (
                    <div key={dateKey}>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4 sticky top-0 bg-white py-1">
                        {dateKey}
                      </h3>
                      <div className="ml-6">
                        {items.map((item, idx) => (
                          <TimelineItemCard key={`${item.type}-${item.date}-${idx}`} item={item} />
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
}
