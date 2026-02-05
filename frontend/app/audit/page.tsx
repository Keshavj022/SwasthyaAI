"use client";

import { useCallback, useEffect, useState } from "react";
import PageContainer from "@/components/PageContainer";
import SafetyBanner from "@/components/SafetyBanner";
import ConfidenceMeter from "@/components/ConfidenceMeter";
import { fetchAuditLogs } from "@/lib/api";
import type { AuditLogEntry } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ConfidenceLevel = "high" | "moderate" | "low" | "very_low";

type PageState =
  | { kind: "loading" }
  | { kind: "loaded"; logs: AuditLogEntry[]; totalResults: number }
  | { kind: "error"; message: string; offline: boolean };

type FilterState = {
  agentName: string;
  minConfidence: string;
  escalationsOnly: boolean;
  hours: number;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toConfidenceLevel(score: number | null): ConfidenceLevel {
  if (score === null) return "low";
  if (score >= 80) return "high";
  if (score >= 50) return "moderate";
  if (score >= 20) return "low";
  return "very_low";
}

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

function formatAgentName(agentName: string | null): string {
  if (!agentName) return "Unknown";
  // Convert snake_case to Title Case
  return agentName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function getActionSummary(entry: AuditLogEntry): string {
  const agent = formatAgentName(entry.agent_name);
  
  if (entry.escalation_triggered) {
    return `${agent} — Escalation triggered: ${entry.escalation_triggered}`;
  }
  
  if (entry.reasoning_summary) {
    // Use first sentence of reasoning summary as action summary
    const firstSentence = entry.reasoning_summary.split(".")[0];
    if (firstSentence.length < 100) {
      return `${agent} — ${firstSentence}`;
    }
    return `${agent} — ${firstSentence.substring(0, 97)}...`;
  }
  
  return `${agent} — AI interaction completed`;
}

function getAgentDisplayName(agentName: string | null): string {
  const displayNames: Record<string, string> = {
    triage: "Triage",
    diagnostic_support: "Diagnostic Support",
    communication: "Communication",
    health_support: "Health Support",
    image_analysis: "Image Analysis",
    voice: "Voice Transcription",
    drug_info: "Drug Information",
    health_memory: "Health Memory",
    explainability: "Explainability",
    safety_wrapper: "Safety Check",
  };
  
  return agentName ? displayNames[agentName] || formatAgentName(agentName) : "Unknown";
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AuditPage() {
  const [state, setState] = useState<PageState>({ kind: "loading" });
  const [filters, setFilters] = useState<FilterState>({
    agentName: "",
    minConfidence: "",
    escalationsOnly: false,
    hours: 24,
  });
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

  // ── Load audit logs ──────────────────────────────────────────────────────
  const loadAuditLogs = useCallback(async () => {
    setState({ kind: "loading" });

    const result = await fetchAuditLogs({
      agent_name: filters.agentName || undefined,
      min_confidence: filters.minConfidence
        ? parseInt(filters.minConfidence, 10)
        : undefined,
      escalations_only: filters.escalationsOnly,
      hours: filters.hours,
      limit: 100,
    });

    if (result.ok) {
      setState({
        kind: "loaded",
        logs: result.data.logs,
        totalResults: result.data.total_results,
      });
    } else {
      setState({
        kind: "error",
        message: result.error,
        offline: result.offline,
      });
    }
  }, [filters]);

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <PageContainer
      title="Audit & Explainability"
      description="Complete record of all AI actions, decisions, and reasoning. Designed for clinician review and compliance."
      icon="📋"
    >
      {/* Offline banner */}
      {!isOnline && (
        <SafetyBanner
          level="warning"
          title="You are offline"
          description="Audit logs cannot be loaded while offline."
        />
      )}

      {/* Error banner */}
      {state.kind === "error" && (
        <SafetyBanner
          level="warning"
          title={
            state.offline
              ? "Offline — audit logs unavailable"
              : "Unable to load audit logs"
          }
          description={state.message}
        />
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">Filter Logs</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label
              htmlFor="agent-filter"
              className="block text-xs font-medium text-gray-700 mb-1"
            >
              Agent
            </label>
            <select
              id="agent-filter"
              value={filters.agentName}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, agentName: e.target.value }))
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            >
              <option value="">All Agents</option>
              <option value="triage">Triage</option>
              <option value="diagnostic_support">Diagnostic Support</option>
              <option value="communication">Communication</option>
              <option value="health_support">Health Support</option>
              <option value="image_analysis">Image Analysis</option>
              <option value="voice">Voice Transcription</option>
              <option value="drug_info">Drug Information</option>
              <option value="health_memory">Health Memory</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="confidence-filter"
              className="block text-xs font-medium text-gray-700 mb-1"
            >
              Minimum Confidence
            </label>
            <select
              id="confidence-filter"
              value={filters.minConfidence}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  minConfidence: e.target.value,
                }))
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            >
              <option value="">Any Confidence</option>
              <option value="80">High (80%+)</option>
              <option value="50">Moderate (50%+)</option>
              <option value="20">Low (20%+)</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="time-filter"
              className="block text-xs font-medium text-gray-700 mb-1"
            >
              Time Range
            </label>
            <select
              id="time-filter"
              value={filters.hours}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  hours: parseInt(e.target.value, 10),
                }))
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            >
              <option value="1">Last Hour</option>
              <option value="24">Last 24 Hours</option>
              <option value="48">Last 48 Hours</option>
              <option value="168">Last Week</option>
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.escalationsOnly}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    escalationsOnly: e.target.checked,
                  }))
                }
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                Escalations Only
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* Results summary */}
      {state.kind === "loaded" && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <p>
            Showing <span className="font-semibold text-gray-900">{state.logs.length}</span>{" "}
            of <span className="font-semibold text-gray-900">{state.totalResults}</span> audit
            entries
          </p>
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
          <p className="text-sm text-gray-600">Loading audit logs...</p>
        </div>
      )}

      {/* Audit log table */}
      {state.kind === "loaded" && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {state.logs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-sm text-gray-500">
                No audit entries found matching the selected filters.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700">
                      Timestamp
                    </th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700">
                      Agent
                    </th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700">
                      Action Summary
                    </th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700">
                      Confidence
                    </th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700">
                      Explanation
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {state.logs.map((entry) => (
                    <tr
                      key={entry.audit_id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      {/* Timestamp */}
                      <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                        <time dateTime={entry.timestamp}>
                          {formatTimestamp(entry.timestamp)}
                        </time>
                      </td>

                      {/* Agent */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {getAgentDisplayName(entry.agent_name)}
                          </span>
                          {entry.escalation_triggered && (
                            <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                              Escalated
                            </span>
                          )}
                          {entry.reviewed && (
                            <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                              Reviewed
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Action Summary */}
                      <td className="px-4 py-3 text-gray-700 max-w-md">
                        {getActionSummary(entry)}
                      </td>

                      {/* Confidence */}
                      <td className="px-4 py-3">
                        {entry.confidence_score !== null ? (
                          <ConfidenceMeter
                            score={entry.confidence_score}
                            level={toConfidenceLevel(entry.confidence_score)}
                            compact
                          />
                        ) : (
                          <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>

                      {/* Explanation */}
                      <td className="px-4 py-3 text-gray-600 max-w-lg">
                        {entry.reasoning_summary ? (
                          <details className="cursor-pointer">
                            <summary className="text-xs text-blue-600 hover:text-blue-700 font-medium">
                              View Explanation
                            </summary>
                            <p className="mt-2 text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">
                              {entry.reasoning_summary}
                            </p>
                          </details>
                        ) : (
                          <span className="text-xs text-gray-400">No explanation available</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Info box */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
        <div className="flex gap-3">
          <svg
            aria-hidden="true"
            className="w-5 h-5 text-blue-600 shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
            />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">About This Audit Trail</p>
            <p className="text-blue-700">
              This page shows every AI action taken by the system, including the reasoning
              behind each decision. All entries are timestamped and include confidence scores.
              Escalated entries are marked for priority review. This audit trail supports
              compliance, quality assurance, and clinical oversight.
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
