import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // Serve the admin UI under /admin-panel/ so all its _next/static assets
  // are prefixed with /admin-panel/_next/ — preventing conflicts with user-ui
  basePath: "/admin-panel",

  // ── API Proxy ───────────────────────────────────────────────────────────────
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
