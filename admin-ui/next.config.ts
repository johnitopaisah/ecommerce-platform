import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // ── API Proxy ───────────────────────────────────────────────────────────────
  // All browser requests to /api/v1/* are proxied server-side to Django.
  // NEXT_PUBLIC_API_URL is never needed — works on any host automatically.
  async rewrites() {
    const apiUrl = process.env.INTERNAL_API_URL || "http://api:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `${apiUrl}/media/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${apiUrl}/static/:path*`,
      },
    ];
  },

  images: {
    unoptimized: true,
    remotePatterns: [
      { protocol: "http", hostname: "**", pathname: "/media/**" },
      { protocol: "https", hostname: "**", pathname: "/media/**" },
    ],
  },
};

export default nextConfig;
