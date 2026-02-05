"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import ConfidenceMeter from "@/components/ConfidenceMeter";
import DisclaimerBox from "@/components/DisclaimerBox";
import { transcribeAudio, sendChatMessage } from "@/lib/api";
import type {
  TranscriptionResponseData,
  QueryResponse,
  ChatResponseData,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Types & constants
// ---------------------------------------------------------------------------

type ConfidenceLevel = "high" | "moderate" | "low" | "very_low";

type RecordingState =
  | { kind: "idle" }
  | { kind: "requesting_permission" }
  | { kind: "permission_denied"; error: string }
  | { kind: "ready" }
  | { kind: "recording"; duration: number }
  | { kind: "processing"; audioBlob: Blob; duration: number }
  | {
    kind: "transcribed";
    audioBlob: Blob;
    duration: number;
    transcription: QueryResponse<TranscriptionResponseData>;
  }
  | {
    kind: "routed";
    audioBlob: Blob;
    duration: number;
    transcription: QueryResponse<TranscriptionResponseData>;
    agentResponse: QueryResponse<ChatResponseData>;
  }
  | { kind: "error"; message: string; offline: boolean };

type TranscriptionMode =
  | "symptom_reporting"
  | "medical_dictation"
  | "voice_query"
  | "general";

const MODE_OPTIONS: Array<{ value: TranscriptionMode; label: string; desc: string }> = [
  {
    value: "symptom_reporting",
    label: "Symptom Reporting",
    desc: "Describe symptoms or health concerns",
  },
  {
    value: "medical_dictation",
    label: "Medical Dictation",
    desc: "Dictate clinical notes or documentation",
  },
  {
    value: "voice_query",
    label: "Voice Query",
    desc: "Ask health-related questions",
  },
  {
    value: "general",
    label: "General",
    desc: "General voice transcription",
  },
] as const;

const USER_ID = "patient_local";
const MAX_RECORDING_DURATION = 300; // 5 minutes

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "moderate";
  if (score >= 0.2) return "low";
  return "very_low";
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function VoicePage() {
  const [state, setState] = useState<RecordingState>({ kind: "idle" });
  const [mode, setMode] = useState<TranscriptionMode>("general");
  const [isOnline, setIsOnline] = useState(true);
  const [transcriptionHistory, setTranscriptionHistory] = useState<
    QueryResponse<TranscriptionResponseData>[]
  >([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

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

  // ── Cleanup on unmount ──────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      // Stop recording if active
      if (mediaRecorderRef.current?.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      // Stop tracks
      streamRef.current?.getTracks().forEach((track) => track.stop());
      // Clear interval
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  // ── Request microphone permission ───────────────────────────────────────
  const requestMicrophoneAccess = useCallback(async () => {
    setState({ kind: "requesting_permission" });

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      setState({ kind: "ready" });
    } catch (err) {
      const error = err as Error;
      let errorMessage = "Microphone access denied or unavailable.";

      if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
        errorMessage =
          "Microphone permission was denied. Please enable microphone access in your browser settings and try again.";
      } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
        errorMessage = "No microphone found. Please connect a microphone and try again.";
      } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
        errorMessage =
          "Microphone is being used by another application. Please close other applications and try again.";
      }

      setState({ kind: "permission_denied", error: errorMessage });
    }
  }, []);

  // ── Start recording ────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    if (!streamRef.current) {
      await requestMicrophoneAccess();
      // Wait a moment for state to update
      await new Promise((resolve) => setTimeout(resolve, 100));
      if (!streamRef.current) return;
    }

    try {
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(streamRef.current, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : MediaRecorder.isTypeSupported("audio/ogg")
            ? "audio/ogg"
            : "audio/wav",
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });
        const duration = (Date.now() - startTimeRef.current) / 1000;

        setState({ kind: "processing", audioBlob, duration });
        processTranscription(audioBlob, duration);
      };

      mediaRecorder.onerror = (event) => {
        setState({
          kind: "error",
          message: "Recording error occurred. Please try again.",
          offline: false,
        });
      };

      mediaRecorder.start();
      startTimeRef.current = Date.now();
      setState({ kind: "recording", duration: 0 });

      // Update duration every second
      durationIntervalRef.current = setInterval(() => {
        setState((prev) => {
          if (prev.kind === "recording") {
            const elapsed = (Date.now() - startTimeRef.current) / 1000;
            if (elapsed >= MAX_RECORDING_DURATION) {
              // Auto-stop at max duration
              mediaRecorder.stop();
              if (durationIntervalRef.current) {
                clearInterval(durationIntervalRef.current);
                durationIntervalRef.current = null;
              }
            }
            return { ...prev, duration: elapsed };
          }
          return prev;
        });
      }, 100);
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof Error ? err.message : "Failed to start recording",
        offline: false,
      });
    }
  }, [requestMicrophoneAccess]);

  // ── Stop recording ───────────────────────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
  }, []);

  // ── Process transcription ───────────────────────────────────────────────
  const processTranscription = useCallback(
    async (audioBlob: Blob, duration: number) => {
      const result = await transcribeAudio(audioBlob, USER_ID, {
        mode,
        language: "en-US",
      });

      if (result.ok) {
        const transcription = result.data;
        setTranscriptionHistory((prev) => [transcription, ...prev]);
        setState({
          kind: "transcribed",
          audioBlob,
          duration,
          transcription,
        });

        // If transcription contains a query, route it through orchestrator
        const transcribedText = transcription.data.transcription.trim();
        if (
          transcribedText.length > 0 &&
          (mode === "voice_query" || mode === "symptom_reporting")
        ) {
          const agentResult = await sendChatMessage(transcribedText, USER_ID);
          if (agentResult.ok) {
            setState({
              kind: "routed",
              audioBlob,
              duration,
              transcription,
              agentResponse: agentResult.data,
            });
          }
        }
      } else {
        setState({
          kind: "error",
          message: result.error,
          offline: result.offline,
        });
      }
    },
    [mode]
  );

  // ── Reset to idle ────────────────────────────────────────────────────────
  const reset = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    setState({ kind: "idle" });
  }, []);

  // ── Render helpers ───────────────────────────────────────────────────────
  const isRecording = state.kind === "recording";
  const isProcessing = state.kind === "processing";
  const hasResults =
    state.kind === "transcribed" || state.kind === "routed";
  const canRecord =
    state.kind === "idle" ||
    state.kind === "ready" ||
    state.kind === "permission_denied" ||
    state.kind === "error";

  return (
    <PageContainer
      title="Voice Interaction"
      description="Clinical dictation and transcription using local speech models. All audio is processed on-device."
      icon="🎙️"
    >
      {/* Offline banner */}
      {!isOnline && (
        <SafetyBanner
          level="warning"
          title="You are offline"
          description="Voice transcription requires a connection to the local inference backend."
        />
      )}

      {/* Error banner */}
      {state.kind === "error" && (
        <SafetyBanner
          level="warning"
          title={
            state.offline
              ? "Offline — transcription unavailable"
              : "Transcription error"
          }
          description={state.message}
        />
      )}

      {/* Permission denied banner */}
      {state.kind === "permission_denied" && (
        <SafetyBanner
          level="warning"
          title="Microphone access required"
          description={state.error}
        />
      )}

      {/* Mandatory disclaimer */}
      <DisclaimerBox
        text="Voice transcription uses automated speech recognition and may contain errors. Always verify medical terminology and critical information before use in clinical documentation."
        category="voice"
      />

      {/* ── Recording controls ───────────────────────────────────── */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            Voice Recording
          </h2>
          <p className="text-sm text-gray-500">
            Select recording mode and press the button to start.
          </p>
        </div>

        {/* Mode selection */}
        <div>
          <label
            htmlFor="recording-mode"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Recording mode
          </label>
          <select
            id="recording-mode"
            value={mode}
            onChange={(e) =>
              setMode(e.target.value as TranscriptionMode)
            }
            disabled={isRecording || isProcessing}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
          >
            {MODE_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label} — {m.desc}
              </option>
            ))}
          </select>
        </div>

        {/* Recording button and status */}
        <div className="flex flex-col items-center py-4">
          {state.kind === "idle" && (
            <button
              type="button"
              onClick={requestMicrophoneAccess}
              disabled={!isOnline}
              className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-8 py-4 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Request microphone access"
            >
              <svg
                aria-hidden="true"
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                />
              </svg>
              Enable Microphone
            </button>
          )}

          {state.kind === "requesting_permission" && (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-blue-600 animate-pulse"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                  />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Requesting microphone access...</p>
            </div>
          )}

          {state.kind === "ready" && (
            <button
              type="button"
              onClick={startRecording}
              disabled={!isOnline}
              className="inline-flex items-center gap-2 rounded-full bg-red-600 px-8 py-4 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Start recording"
            >
              <svg
                aria-hidden="true"
                className="w-6 h-6"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <circle cx="12" cy="12" r="6" />
              </svg>
              Start Recording
            </button>
          )}

          {isRecording && (
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="w-24 h-24 rounded-full bg-red-100 flex items-center justify-center animate-pulse">
                  <svg
                    className="w-12 h-12 text-red-600"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <circle cx="12" cy="12" r="6" />
                  </svg>
                </div>
                <div className="absolute inset-0 rounded-full border-4 border-red-600 animate-ping opacity-20" />
              </div>
              <div className="text-center">
                <p className="text-2xl font-mono font-semibold text-gray-900">
                  {formatDuration(state.duration)}
                </p>
                <p className="text-sm text-gray-500 mt-1">Recording in progress</p>
              </div>
              <button
                type="button"
                onClick={stopRecording}
                className="inline-flex items-center gap-2 rounded-lg bg-gray-100 px-6 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2 transition-colors"
                aria-label="Stop recording"
              >
                <svg
                  aria-hidden="true"
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5.25 7.5A2.25 2.25 0 0 1 7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9Z"
                  />
                </svg>
                Stop Recording
              </button>
            </div>
          )}

          {isProcessing && (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-blue-600 animate-spin"
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
              <p className="text-sm text-gray-600">
                Processing audio... This may take a moment.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Transcription results ───────────────────────────────── */}
      {hasResults && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              Transcription Results
            </h2>
            <button
              type="button"
              onClick={reset}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              New Recording
            </button>
          </div>

          {/* Transcription */}
          <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-gray-900 mb-2">
                  Transcribed Text
                </h3>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {state.transcription.data.transcription}
                </p>
                <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                  <span>
                    Duration: {formatDuration(state.duration)}
                  </span>
                  <span>
                    Mode: {state.transcription.data.mode}
                  </span>
                  <span>
                    Language: {state.transcription.data.language}
                  </span>
                </div>
              </div>
              {state.transcription.confidence && (
                <ConfidenceMeter
                  score={Math.round(state.transcription.confidence.score * 100)}
                  level={toConfidenceLevel(state.transcription.confidence.score)}
                  compact
                />
              )}
            </div>

            {/* Confidence details */}
            {state.transcription.data.confidence && (
              <div className="pt-4 border-t border-gray-200">
                <ConfidenceMeter
                  score={Math.round(state.transcription.data.confidence * 100)}
                  level={toConfidenceLevel(state.transcription.data.confidence)}
                />
              </div>
            )}

            {/* Medical terms */}
            {state.transcription.data.medical_terms_identified?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">
                  Medical terms identified
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {state.transcription.data.medical_terms_identified.map(
                    (term, i) => (
                      <span
                        key={i}
                        className="inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs text-blue-700"
                      >
                        {term}
                      </span>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Alternative transcriptions */}
            {state.transcription.data.alternative_transcriptions?.length > 0 && (
              <details className="pt-2">
                <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700">
                  Alternative transcriptions ({state.transcription.data.alternative_transcriptions.length})
                </summary>
                <ul className="mt-2 space-y-1">
                  {state.transcription.data.alternative_transcriptions.map(
                    (alt, i) => (
                      <li
                        key={i}
                        className="text-xs text-gray-600 pl-4 border-l-2 border-gray-200"
                      >
                        {alt}
                      </li>
                    )
                  )}
                </ul>
              </details>
            )}
          </div>

          {/* Routed agent response */}
          {state.kind === "routed" && state.agentResponse && (
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-gray-900">
                  Agent Response
                </h3>
                {state.agentResponse.agent && (
                  <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                    {state.agentResponse.agent}
                  </span>
                )}
              </div>
              {state.agentResponse.data.response && (
                <p className="text-sm text-gray-700 leading-relaxed">
                  {state.agentResponse.data.response}
                </p>
              )}
              {state.agentResponse.data.recommendations &&
                state.agentResponse.data.recommendations.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">
                      Recommendations
                    </p>
                    <ul className="space-y-1">
                      {state.agentResponse.data.recommendations.map((rec, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm text-gray-700"
                        >
                          <span className="text-gray-400 shrink-0 mt-0.5">
                            &#8227;
                          </span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}

          {/* Next action */}
          {state.transcription.data.next_action && (
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
              <p className="text-sm text-blue-800">
                {state.transcription.data.next_action}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Transcription history ─────────────────────────────────── */}
      {transcriptionHistory.length > 0 && !hasResults && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Transcription History
          </h2>
          <div className="space-y-3">
            {transcriptionHistory.slice(0, 5).map((item, i) => (
              <div
                key={i}
                className="border border-gray-200 rounded-lg p-3 text-sm"
              >
                <div className="flex items-start justify-between gap-3 mb-1">
                  <p className="text-gray-700 flex-1 line-clamp-2">
                    {item.data.transcription}
                  </p>
                  {item.confidence && (
                    <ConfidenceMeter
                      score={Math.round(item.confidence.score * 100)}
                      level={toConfidenceLevel(item.confidence.score)}
                      compact
                    />
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 mt-2">
                  <span>{item.data.mode}</span>
                  <span>&middot;</span>
                  <span>{formatDuration(item.data.audio_duration_seconds)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
