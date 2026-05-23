import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const projectRoot = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: projectRoot,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/api/:path*`,
      },
      {
        source: "/health/backend",
        destination: `${apiBaseUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
