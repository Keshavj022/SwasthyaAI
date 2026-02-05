"use client";

import {
  forwardRef,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import ConfidenceMeter from "@/components/ConfidenceMeter";
import DisclaimerBox from "@/components/DisclaimerBox";
import { uploadImage } from "@/lib/api";
import type { ImageResponseData, QueryResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types & constants
// ---------------------------------------------------------------------------

type ConfidenceLevel = "high" | "moderate" | "low" | "very_low";

type PageState =
  | { kind: "idle" }
  | { kind: "preview"; file: File; previewUrl: string }
  | { kind: "loading"; file: File; previewUrl: string }
  | {
      kind: "results";
      file: File;
      previewUrl: string;
      response: QueryResponse<ImageResponseData>;
    }
  | { kind: "error"; message: string; offline: boolean };

const MODALITIES = [
  { value: "chest_xray", label: "Chest X-ray" },
  { value: "ct_chest", label: "CT \u2014 Chest" },
  { value: "ct_head", label: "CT \u2014 Head" },
  { value: "ct_abdomen", label: "CT \u2014 Abdomen" },
  { value: "mri_brain", label: "MRI \u2014 Brain" },
  { value: "dermatology", label: "Dermatology" },
  { value: "pathology", label: "Pathology" },
  { value: "other", label: "Other / Unknown" },
] as const;

const ANALYSIS_TYPES = [
  {
    value: "finding_detection" as const,
    label: "Finding Detection",
    desc: "Identify and describe observable findings",
  },
  {
    value: "abnormality_classification" as const,
    label: "Abnormality Classification",
    desc: "Classify detected abnormalities",
  },
  {
    value: "region_description" as const,
    label: "Region Description",
    desc: "Describe a specific anatomical region",
  },
] as const;

const ACCEPTED_TYPES = ["image/png", "image/jpeg"];
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB

const USER_ID = "patient_local";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "moderate";
  if (score >= 0.2) return "low";
  return "very_low";
}

function isConfidenceLevel(v: string | undefined): v is ConfidenceLevel {
  return !!v && ["high", "moderate", "low", "very_low"].includes(v);
}

const severityColor: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  moderate: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
  normal: "bg-gray-100 text-gray-700",
};

function severityBadge(severity: string) {
  const cls =
    severityColor[severity.toLowerCase()] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}
    >
      {severity}
    </span>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FindingCard({
  finding,
  index,
}: {
  finding: ImageResponseData["findings"][number];
  index: number;
}) {
  const pct = Math.round(finding.confidence * 100);
  const level = toConfidenceLevel(finding.confidence);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2.5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-gray-400">
              #{index + 1}
            </span>
            <h4 className="text-sm font-semibold text-gray-900">
              {finding.finding}
            </h4>
            {severityBadge(finding.severity)}
          </div>
          {finding.location && (
            <p className="text-xs text-gray-500 mt-0.5">
              Location: {finding.location}
              {finding.size ? ` \u00b7 Size: ${finding.size}` : ""}
            </p>
          )}
        </div>
        <ConfidenceMeter score={pct} level={level} compact />
      </div>

      {/* Description */}
      {finding.description && (
        <p className="text-sm text-gray-700 leading-relaxed">
          {finding.description}
        </p>
      )}

      {/* Differential */}
      {finding.differential.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">
            Differential considerations
          </p>
          <div className="flex flex-wrap gap-1.5">
            {finding.differential.map((d, i) => (
              <span
                key={i}
                className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-700"
              >
                {d}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results panel (extracted for readability)
// ---------------------------------------------------------------------------

const ResultsPanel = forwardRef<
  HTMLDivElement,
  {
    response: QueryResponse<ImageResponseData>;
    previewUrl: string;
    fileName: string;
  }
>(function ResultsPanel({ response, previewUrl, fileName }, ref) {
  const d = response.data;
  const overallLevel = response.confidence?.level;
  const overallScore = response.confidence?.score ?? 0;

  return (
    <div ref={ref} className="space-y-5">
      {/* Two-column: preview + meta */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Image preview */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="bg-gray-900 flex items-center justify-center min-h-[280px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt={`Uploaded medical image: ${fileName}`}
              className="max-h-[400px] w-auto object-contain"
            />
          </div>
          <div className="px-4 py-3 text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>Modality</span>
              <span className="font-medium text-gray-700">
                {d.modality?.replace(/_/g, " ") ?? "Unknown"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Analysis</span>
              <span className="font-medium text-gray-700">
                {d.analysis_type?.replace(/_/g, " ") ?? "Finding detection"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Image quality</span>
              <span className="font-medium text-gray-700">
                {d.image_quality ?? "N/A"}
              </span>
            </div>
          </div>
        </div>

        {/* Right column: impression + confidence + findings */}
        <div className="lg:col-span-3 space-y-4">
          {/* Overall confidence */}
          {response.confidence && isConfidenceLevel(overallLevel) && (
            <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
              <ConfidenceMeter score={overallScore} level={overallLevel} />
            </div>
          )}

          {/* Overall impression */}
          {d.overall_impression && (
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-1.5">
                Overall Impression
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                {d.overall_impression}
              </p>
            </div>
          )}

          {/* Limitations */}
          {d.limitations.length > 0 && (
            <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
              <h3 className="text-xs font-semibold text-yellow-800 mb-1">
                Analysis Limitations
              </h3>
              <ul className="space-y-0.5">
                {d.limitations.map((l, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-1.5 text-xs text-yellow-800"
                  >
                    <span className="shrink-0 mt-0.5">&#8227;</span>
                    {l}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Findings list */}
      {d.findings.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-gray-900">
            Identified Findings for Clinical Review
          </h2>
          <p className="text-xs text-gray-500 -mt-1">
            Each finding requires independent verification by a qualified
            specialist. Confidence reflects algorithmic certainty, not clinical
            significance.
          </p>
          {d.findings.map((f, i) => (
            <FindingCard key={i} finding={f} index={i} />
          ))}
        </div>
      )}

      {d.findings.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm text-center">
          <p className="text-sm text-gray-500">
            No discrete findings were detected. This does not exclude the
            presence of pathology. Clinical correlation is required.
          </p>
        </div>
      )}

      {/* Regions of interest */}
      {d.regions_of_interest.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Regions of Interest
          </h3>
          <div className="space-y-2">
            {d.regions_of_interest.map((r, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 text-xs font-mono text-gray-600">
                  {r.region}
                </span>
                <p className="text-gray-700">{r.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clinical correlation */}
      {d.clinical_correlation.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Clinical Correlation Required
          </h3>
          <ul className="space-y-1">
            {d.clinical_correlation.map((c, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-gray-400 shrink-0 mt-0.5">&#8227;</span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended next steps */}
      {d.recommended_next_steps.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Suggested Next Steps
          </h3>
          <ul className="space-y-1">
            {d.recommended_next_steps.map((s, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-gray-400 shrink-0 mt-0.5">&#8227;</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Mandatory disclaimer — always visible */}
      <DisclaimerBox
        text={
          response.disclaimer ||
          d.disclaimer ||
          "This AI-generated analysis is for clinician review only. It does not constitute a radiological diagnosis. Images must be interpreted by qualified radiologists or specialists."
        }
        category="image_analysis"
      />
    </div>
  );
});

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ImagingPage() {
  const [state, setState] = useState<PageState>({ kind: "idle" });
  const [modality, setModality] = useState("chest_xray");
  const [analysisType, setAnalysisType] =
    useState<(typeof ANALYSIS_TYPES)[number]["value"]>("finding_detection");
  const [clinicalContext, setClinicalContext] = useState("");
  const [isOnline, setIsOnline] = useState(true);
  const [fileError, setFileError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // ── Online / offline ───────────────────────────────────────────────────
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

  // ── Revoke object URL on unmount or state change ───────────────────────
  useEffect(() => {
    return () => {
      if (
        state.kind === "preview" ||
        state.kind === "loading" ||
        state.kind === "results"
      ) {
        URL.revokeObjectURL(state.previewUrl);
      }
    };
  }, [state]);

  // ── File validation ────────────────────────────────────────────────────
  const validateAndStage = useCallback(
    (file: File | null | undefined) => {
      setFileError(null);
      if (!file) return;

      if (!ACCEPTED_TYPES.includes(file.type)) {
        setFileError(
          `Unsupported file type. Use PNG or JPEG only.`
        );
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setFileError(
          `File is ${formatFileSize(file.size)}. Maximum allowed size is ${formatFileSize(MAX_FILE_SIZE)}.`
        );
        return;
      }

      // Clean up previous preview URL
      if (
        state.kind === "preview" ||
        state.kind === "loading" ||
        state.kind === "results"
      ) {
        URL.revokeObjectURL(state.previewUrl);
      }

      const previewUrl = URL.createObjectURL(file);
      setState({ kind: "preview", file, previewUrl });
    },
    [state]
  );

  // ── Drag & drop ────────────────────────────────────────────────────────
  const [isDragging, setIsDragging] = useState(false);

  const onDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!isOnline) return;
      setIsDragging(true);
    },
    [isOnline]
  );
  const onDragLeave = useCallback(() => setIsDragging(false), []);
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (!isOnline) return;
      validateAndStage(e.dataTransfer.files[0]);
    },
    [isOnline, validateAndStage]
  );

  // ── Submit ─────────────────────────────────────────────────────────────
  const handleAnalyze = useCallback(async () => {
    if (state.kind !== "preview") return;

    setState({ kind: "loading", file: state.file, previewUrl: state.previewUrl });

    const result = await uploadImage(state.file, USER_ID, {
      modality,
      analysisType,
      clinicalContext: clinicalContext.trim() || undefined,
    });

    if (result.ok) {
      setState({
        kind: "results",
        file: state.file,
        previewUrl: state.previewUrl,
        response: result.data,
      });
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
  }, [state, modality, analysisType, clinicalContext]);

  const handleReset = useCallback(() => {
    if (
      state.kind === "preview" ||
      state.kind === "loading" ||
      state.kind === "results"
    ) {
      URL.revokeObjectURL(state.previewUrl);
    }
    setState({ kind: "idle" });
    setClinicalContext("");
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [state]);

  // ── Render ─────────────────────────────────────────────────────────────
  const showUploadZone = state.kind === "idle" || state.kind === "error";
  const hasPreview =
    state.kind === "preview" ||
    state.kind === "loading" ||
    state.kind === "results";

  return (
    <PageContainer
      title="Medical Image Analysis"
      description="On-device vision model analysis. All images remain local and are never transmitted externally."
      icon="🏥"
    >
      {/* Offline banner */}
      {!isOnline && (
        <SafetyBanner
          level="warning"
          title="You are offline"
          description="Image analysis requires a connection to the local inference backend."
        />
      )}

      {/* Error banner */}
      {state.kind === "error" && (
        <SafetyBanner
          level="warning"
          title={
            state.offline
              ? "Offline \u2014 analysis unavailable"
              : "Analysis could not be completed"
          }
          description={state.message}
        />
      )}

      {/* Mandatory medical disclaimer — prominent, always visible */}
      <DisclaimerBox
        text="AI image analysis is for clinical decision support only. It does not constitute a radiological diagnosis. All findings must be verified by a qualified radiologist or specialist before clinical use."
        category="image_analysis"
      />

      {/* ── Upload zone ──────────────────────────────────────────── */}
      {showUploadZone && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-5">
          <h2 className="text-lg font-semibold text-gray-900">
            Upload Medical Image
          </h2>

          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => isOnline && fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                isOnline && fileInputRef.current?.click();
              }
            }}
            aria-label="Upload medical image"
            className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
              ${isDragging ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
              ${!isOnline ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            <svg
              aria-hidden="true"
              className="mx-auto w-10 h-10 text-gray-300 mb-3"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-600">
              {isDragging
                ? "Drop image here"
                : "Drag and drop a medical image, or click to browse"}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              PNG or JPEG \u00b7 Max 25 MB
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={(e) => validateAndStage(e.target.files?.[0])}
            />
          </div>

          {fileError && (
            <p className="text-sm text-red-600" role="alert">
              {fileError}
            </p>
          )}
        </div>
      )}

      {/* ── Preview + options ────────────────────────────────────── */}
      {hasPreview && state.kind !== "results" && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {/* Preview */}
          <div className="bg-gray-900 flex items-center justify-center min-h-[220px] max-h-[360px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={state.previewUrl}
              alt={`Preview: ${state.file.name}`}
              className="max-h-[360px] w-auto object-contain"
            />
          </div>

          {/* File info bar */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-500">
            <span className="truncate max-w-[60%]">{state.file.name}</span>
            <div className="flex items-center gap-3">
              <span>{formatFileSize(state.file.size)}</span>
              <button
                type="button"
                onClick={handleReset}
                className="text-red-500 hover:text-red-700 font-medium"
              >
                Remove
              </button>
            </div>
          </div>

          {/* Options form */}
          <div className="p-5 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="modality"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Imaging modality
                </label>
                <select
                  id="modality"
                  value={modality}
                  onChange={(e) => setModality(e.target.value)}
                  disabled={state.kind === "loading"}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  {MODALITIES.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="analysisType"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Analysis type
                </label>
                <select
                  id="analysisType"
                  value={analysisType}
                  onChange={(e) =>
                    setAnalysisType(
                      e.target.value as (typeof ANALYSIS_TYPES)[number]["value"]
                    )
                  }
                  disabled={state.kind === "loading"}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  {ANALYSIS_TYPES.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label
                htmlFor="clinicalContext"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Clinical context{" "}
                <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                id="clinicalContext"
                rows={2}
                value={clinicalContext}
                onChange={(e) => setClinicalContext(e.target.value)}
                placeholder="e.g. 65-year-old male, persistent cough, history of smoking"
                disabled={state.kind === "loading"}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={state.kind === "loading" || !isOnline}
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
                    Analyzing Image\u2026
                  </>
                ) : (
                  "Request Image Analysis"
                )}
              </button>
              <button
                type="button"
                onClick={handleReset}
                disabled={state.kind === "loading"}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────────── */}
      {state.kind === "results" && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              Analysis Results
            </h2>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              New Analysis
            </button>
          </div>
          <ResultsPanel
            ref={resultsRef}
            response={state.response}
            previewUrl={state.previewUrl}
            fileName={state.file.name}
          />
        </>
      )}
    </PageContainer>
  );
}
