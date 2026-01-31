"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  application: string;
  version: string;
  environment: string;
  timestamp: string;
  database: {
    status: string;
    file_exists: boolean;
    type: string;
  };
  offline_mode: {
    enabled: boolean;
    description: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/health");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect to backend");
        setHealth(null);
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
    // Refresh health status every 10 seconds
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-8 pb-20 sm:p-20">
      <main className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">
            Offline-First Hospital AI System
          </h1>
          <p className="text-gray-600">
            Clinical Decision Support System (CDSS) - Privacy-Preserving Healthcare AI
          </p>
        </div>

        {loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <p className="text-blue-800">Connecting to backend...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-red-800 mb-2">
              Backend Connection Error
            </h2>
            <p className="text-red-700 mb-4">{error}</p>
            <div className="bg-white rounded p-4 text-sm">
              <p className="font-semibold mb-2">Troubleshooting:</p>
              <ol className="list-decimal list-inside space-y-1 text-gray-700">
                <li>Ensure the FastAPI backend is running on port 8000</li>
                <li>Run: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && python main.py</code></li>
                <li>Check for port conflicts</li>
              </ol>
            </div>
          </div>
        )}

        {health && (
          <div className="space-y-6">
            {/* System Status Card */}
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <span className={`inline-block w-3 h-3 rounded-full ${
                  health.status === "healthy" ? "bg-green-500" : "bg-yellow-500"
                }`}></span>
                System Status
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Application</p>
                  <p className="font-semibold">{health.application}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Version</p>
                  <p className="font-semibold">{health.version}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Environment</p>
                  <p className="font-semibold">{health.environment}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className={`font-semibold ${
                    health.status === "healthy" ? "text-green-600" : "text-yellow-600"
                  }`}>
                    {health.status.toUpperCase()}
                  </p>
                </div>
              </div>
            </div>

            {/* Database Status Card */}
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h2 className="text-2xl font-semibold mb-4">Database</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Type</span>
                  <span className="font-semibold">{health.database.type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Status</span>
                  <span className={`font-semibold ${
                    health.database.status === "connected" ? "text-green-600" : "text-red-600"
                  }`}>
                    {health.database.status}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">File Exists</span>
                  <span className={`font-semibold ${
                    health.database.file_exists ? "text-green-600" : "text-yellow-600"
                  }`}>
                    {health.database.file_exists ? "Yes" : "No (will be created)"}
                  </span>
                </div>
              </div>
            </div>

            {/* Offline Mode Card */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">📡</span>
                Offline Mode
              </h2>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Enabled</span>
                  <span className="font-semibold text-blue-700">
                    {health.offline_mode.enabled ? "YES" : "NO"}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mt-2">
                  {health.offline_mode.description}
                </p>
              </div>
            </div>

            {/* Safety Notice */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-2 text-yellow-800">
                ⚠️ Clinical Decision Support Notice
              </h2>
              <p className="text-sm text-yellow-800">
                This system provides clinical decision support and is NOT a replacement
                for professional medical judgment. All AI-generated suggestions require
                review by licensed healthcare professionals. See{" "}
                <a href="/SAFETY_AND_SCOPE.md" className="underline font-semibold">
                  SAFETY_AND_SCOPE.md
                </a>{" "}
                for complete safety boundaries.
              </p>
            </div>

            {/* Quick Links */}
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h2 className="text-2xl font-semibold mb-4">Quick Links</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-4 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors"
                >
                  <p className="font-semibold text-blue-800">API Documentation</p>
                  <p className="text-sm text-blue-600">OpenAPI/Swagger UI</p>
                </a>
                <a
                  href="http://127.0.0.1:8000"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-4 bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 transition-colors"
                >
                  <p className="font-semibold text-green-800">Backend API</p>
                  <p className="text-sm text-green-600">FastAPI Root</p>
                </a>
              </div>
            </div>

            {/* Footer Info */}
            <div className="text-center text-sm text-gray-500 mt-8">
              <p>Last updated: {new Date(health.timestamp).toLocaleString()}</p>
              <p className="mt-1">Auto-refreshes every 10 seconds</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
