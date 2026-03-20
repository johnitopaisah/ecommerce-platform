import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // ── API Proxy ───────────────────────────────────────────────────────────────
  // All browser requests to /api/v1/* are proxied server-side to Django.
  // This means NEXT_PUBLIC_API_URL is never needed — the browser always
  // calls the same host it loaded from, regardless of where the app is deployed.
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
