"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import ConfidenceMeter from "@/components/ConfidenceMeter";
import DisclaimerBox from "@/components/DisclaimerBox";
import { runDiagnostics } from "@/lib/api";
import type { DiagnosticResponseData, QueryResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ConfidenceLevel = "high" | "moderate" | "low" | "very_low";

type PageState =
  | { kind: "idle" }
  | { kind: "loading" }
  | {
      kind: "results";
      response: QueryResponse<DiagnosticResponseData>;
    }
  | { kind: "error"; message: string; offline: boolean };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map a 0-1 float to the backend's four-tier confidence level. */
function toConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "moderate";
  if (score >= 0.2) return "low";
  return "very_low";
}

const USER_ID = "patient_local";

const DURATION_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "hours", label: "Hours (acute onset)" },
  { value: "days", label: "Days" },
  { value: "1-2 weeks", label: "1\u20132 weeks" },
  { value: "weeks", label: "Several weeks" },
  { value: "months", label: "Months (chronic)" },
] as const;

const SEVERITY_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "mild", label: "Mild" },
  { value: "moderate", label: "Moderate" },
  { value: "severe", label: "Severe" },
] as const;

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DiagnosisCard({
  dx,
}: {
  dx: DiagnosticResponseData["differential_diagnoses"][number];
}) {
  const pct = Math.round(dx.confidence * 100);
  const level = toConfidenceLevel(dx.confidence);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-400">
              #{dx.rank}
            </span>
            <h4 className="text-sm font-semibold text-gray-900 truncate">
              {dx.condition}
            </h4>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Relative likelihood: {dx.likelihood}
          </p>
        </div>
        <ConfidenceMeter score={pct} level={level} compact />
      </div>

      {/* Detail grid */}
      <dl className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        {dx.supporting_features && (
          <div>
            <dt className="font-medium text-gray-500 mb-0.5">
              Supporting features
            </dt>
            <dd className="text-gray-700">{dx.supporting_features}</dd>
          </div>
        )}
        {dx.contradicting_features && (
          <div>
            <dt className="font-medium text-gray-500 mb-0.5">
              Contradicting features
            </dt>
            <dd className="text-gray-700">{dx.contradicting_features}</dd>
          </div>
        )}
        {dx.missing_information && (
          <div>
            <dt className="font-medium text-gray-500 mb-0.5">
              Additional information needed
            </dt>
            <dd className="text-gray-700">{dx.missing_information}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DiagnosticsPage() {
  // ── form fields ────────────────────────────────────────────────────────
  const [symptoms, setSymptoms] = useState("");
  const [duration, setDuration] = useState("");
  const [severity, setSeverity] = useState("");
  const [showVitals, setShowVitals] = useState(false);
  const [heartRate, setHeartRate] = useState("");
  const [bpSystolic, setBpSystolic] = useState("");
  const [bpDiastolic, setBpDiastolic] = useState("");
  const [temperature, setTemperature] = useState("");
  const [respRate, setRespRate] = useState("");
  const [o2Sat, setO2Sat] = useState("");

  // ── page state ─────────────────────────────────────────────────────────
  const [state, setState] = useState<PageState>({ kind: "idle" });
  const [isOnline, setIsOnline] = useState(true);
  const resultsRef = useRef<HTMLDivElement>(null);

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

  // ── submit handler ─────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    const parsed = symptoms
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (parsed.length === 0) return;

    setState({ kind: "loading" });

    const numOrUndefined = (v: string) => {
      const n = Number(v);
      return v && !Number.isNaN(n) ? n : undefined;
    };

    const vitalSigns =
      heartRate || bpSystolic || bpDiastolic || temperature || respRate || o2Sat
        ? {
            heart_rate: numOrUndefined(heartRate),
            blood_pressure_systolic: numOrUndefined(bpSystolic),
            blood_pressure_diastolic: numOrUndefined(bpDiastolic),
            temperature: numOrUndefined(temperature),
            respiratory_rate: numOrUndefined(respRate),
            oxygen_saturation: numOrUndefined(o2Sat),
          }
        : undefined;

    const result = await runDiagnostics(
      {
        symptoms: parsed,
        duration: duration || undefined,
        severity: severity || undefined,
        vitalSigns,
      },
      USER_ID
    );

    if (result.ok) {
      setState({ kind: "results", response: result.data });
      requestAnimationFrame(() =>
        resultsRef.current?.scrollIntoView({ behavior: "smooth" })
      );
    } else {
      setState({
        kind: "error",
        message: result.error,
        offline: result.offline,
      });
    }
  }, [
    symptoms,
    duration,
    severity,
    heartRate,
    bpSystolic,
    bpDiastolic,
    temperature,
    respRate,
    o2Sat,
  ]);

  const canSubmit =
    symptoms.trim().length > 0 && state.kind !== "loading" && isOnline;

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <PageContainer
      title="Diagnostic Support"
      description="Differential diagnosis decision support. All suggestions require review by a licensed clinician."
      icon="🔬"
    >
      {/* ── Offline banner ───────────────────────────────────────── */}
      {!isOnline && (
        <SafetyBanner
          level="warning"
          title="You are offline"
          description="Diagnostic analysis requires a connection to the local inference backend."
        />
      )}

      {/* ── Symptom input form ───────────────────────────────────── */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-5"
      >
        <h2 className="text-lg font-semibold text-gray-900">
          New Clinical Assessment
        </h2>

        {/* Symptoms */}
        <div>
          <label
            htmlFor="symptoms"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Presenting symptoms{" "}
            <span className="text-gray-400 font-normal">
              (comma-separated)
            </span>
          </label>
          <textarea
            id="symptoms"
            rows={3}
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. persistent cough, fever, fatigue, shortness of breath"
            disabled={state.kind === "loading" || !isOnline}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
          />
        </div>

        {/* Duration + Severity row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="duration"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Duration of symptoms
            </label>
            <select
              id="duration"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              disabled={state.kind === "loading" || !isOnline}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              {DURATION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="severity"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Reported severity
            </label>
            <select
              id="severity"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              disabled={state.kind === "loading" || !isOnline}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              {SEVERITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Vital signs (collapsible) */}
        <div>
          <button
            type="button"
            onClick={() => setShowVitals((v) => !v)}
            className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            <svg
              aria-hidden="true"
              className={`w-4 h-4 transition-transform ${showVitals ? "rotate-90" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m8.25 4.5 7.5 7.5-7.5 7.5"
              />
            </svg>
            Vital signs (optional)
          </button>

          {showVitals && (
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                {
                  id: "hr",
                  label: "Heart rate (bpm)",
                  value: heartRate,
                  set: setHeartRate,
                },
                {
                  id: "bps",
                  label: "BP systolic (mmHg)",
                  value: bpSystolic,
                  set: setBpSystolic,
                },
                {
                  id: "bpd",
                  label: "BP diastolic (mmHg)",
                  value: bpDiastolic,
                  set: setBpDiastolic,
                },
                {
                  id: "temp",
                  label: "Temperature (\u00b0F)",
                  value: temperature,
                  set: setTemperature,
                },
                {
                  id: "rr",
                  label: "Resp. rate (/min)",
                  value: respRate,
                  set: setRespRate,
                },
                {
                  id: "o2",
                  label: "O\u2082 saturation (%)",
                  value: o2Sat,
                  set: setO2Sat,
                },
              ].map((v) => (
                <div key={v.id}>
                  <label
                    htmlFor={v.id}
                    className="block text-xs font-medium text-gray-500 mb-0.5"
                  >
                    {v.label}
                  </label>
                  <input
                    id={v.id}
                    type="number"
                    inputMode="decimal"
                    value={v.value}
                    onChange={(e) => v.set(e.target.value)}
                    disabled={state.kind === "loading" || !isOnline}
                    className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {state.kind === "loading" ? (
            <>
              <svg
                className="w-4 h-4 animate-spin"
                aria-hidden="true"
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
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Analyzing…
            </>
          ) : (
            "Request Clinical Assessment"
          )}
        </button>
      </form>

      {/* ── Error fallback ───────────────────────────────────────── */}
      {state.kind === "error" && (
        <SafetyBanner
          level={state.offline ? "warning" : "warning"}
          title={
            state.offline
              ? "Offline — analysis unavailable"
              : "Assessment could not be completed"
          }
          description={state.message}
        />
      )}

      {/* ── Results ──────────────────────────────────────────────── */}
      {state.kind === "results" && (
        <ResultsSection ref={resultsRef} response={state.response} />
      )}
    </PageContainer>
  );
}

// ---------------------------------------------------------------------------
// Results section (extracted for clarity)
// ---------------------------------------------------------------------------

import { forwardRef } from "react";

const ResultsSection = forwardRef<
  HTMLDivElement,
  { response: QueryResponse<DiagnosticResponseData> }
>(function ResultsSection({ response }, ref) {
  const d = response.data;
  const overallLevel = response.confidence?.level;
  const overallScore = response.confidence?.score ?? 0;

  const isValidLevel = (v: string | undefined): v is ConfidenceLevel =>
    !!v && ["high", "moderate", "low", "very_low"].includes(v);

  return (
    <div ref={ref} className="space-y-5">
      {/* Emergency alert */}
      {(response.emergency || d.emergency_detected) && (
        <SafetyBanner
          level="emergency"
          title="Emergency indicators identified"
          description="The reported symptoms contain patterns associated with potentially life-threatening conditions. Immediate clinical evaluation is strongly advised."
          redFlags={d.red_flags}
        />
      )}

      {/* Red flags (non-emergency) */}
      {!response.emergency &&
        !d.emergency_detected &&
        d.red_flags.length > 0 && (
          <SafetyBanner
            level="warning"
            title="Clinical red flags identified"
            description="The following findings may warrant further urgent evaluation."
            redFlags={d.red_flags}
          />
        )}

      {/* Overall confidence */}
      {response.confidence && isValidLevel(overallLevel) && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <ConfidenceMeter score={overallScore} level={overallLevel} />
        </div>
      )}

      {/* Differential findings */}
      {d.differential_diagnoses.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-gray-900">
            Possible Conditions for Clinical Consideration
          </h2>
          <p className="text-xs text-gray-500 -mt-1">
            Ranked by relative likelihood based on reported symptoms.
            Clinical correlation is required for all entries.
          </p>
          {d.differential_diagnoses.map((dx) => (
            <DiagnosisCard key={dx.rank} dx={dx} />
          ))}
        </div>
      )}

      {/* Suggested additional evaluation */}
      {d.recommended_workup.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Suggested Additional Evaluation
          </h3>
          <ul className="space-y-1">
            {d.recommended_workup.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-gray-400 shrink-0 mt-0.5">&#8227;</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clinical correlation */}
      {d.clinical_correlation_needed.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Clinical Correlation Required
          </h3>
          <ul className="space-y-1">
            {d.clinical_correlation_needed.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-gray-400 shrink-0 mt-0.5">&#8227;</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Symptoms analyzed */}
      {d.symptoms_analyzed.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Symptoms Analyzed
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {d.symptoms_analyzed.map((s, i) => (
              <span
                key={i}
                className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Mandatory disclaimer — always visible, never collapsible */}
      <DisclaimerBox
        text={
          response.disclaimer ||
          d.disclaimer ||
          "This assessment is generated by an AI system and does not constitute a medical diagnosis. All findings require independent review and clinical correlation by a licensed healthcare professional."
        }
        category="diagnostic"
      />
    </div>
  );
});
