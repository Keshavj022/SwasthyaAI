import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Offline-first PWA configuration (future)
  // Currently minimal config for local development

  // API proxy to FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
