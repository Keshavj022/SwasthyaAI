/**
 * API client for communicating with FastAPI backend.
 * Designed for offline-first operation with graceful degradation.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`API request failed: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * Health check endpoint
   */
  async getHealth() {
    return this.request<{
      status: string;
      application: string;
      version: string;
      timestamp: string;
    }>("/api/health");
  }

  /**
   * Ping endpoint for quick connectivity test
   */
  async ping() {
    return this.request<{ message: string; timestamp: string }>(
      "/api/health/ping"
    );
  }

  // Future: Add agent-specific API methods here
  // - Diagnostic support
  // - Image analysis
  // - Drug interaction checks
  // - Appointment scheduling
  // etc.
}

// Export singleton instance
export const apiClient = new APIClient();
