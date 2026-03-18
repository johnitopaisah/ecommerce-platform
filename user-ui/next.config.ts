import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Allow images served from the local Django API in development.
    // Next.js 16 blocks localhost by default as it's a private IP.
    // In production this is replaced by S3/CDN URLs.
    unoptimized: process.env.NODE_ENV === "development",
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "http",
        hostname: "10.*",
        pathname: "/media/**",
      },
    ],
  },
  // Required for standalone Docker build in Phase 6
  output: "standalone",
};

export default nextConfig;
