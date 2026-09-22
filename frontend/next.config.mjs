import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));
const backendApiUrl = (
  process.env.AUSA_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
  typescript: {
    ignoreBuildErrors: false,
  },
  turbopack: {
    root: projectRoot,
  },
  allowedDevOrigins: ["127.0.0.1"],
  async rewrites() {
    return [{
      source: "/api/v1/:path*",
      destination: `${backendApiUrl}/:path*`,
    }];
  },
};

export default nextConfig;
