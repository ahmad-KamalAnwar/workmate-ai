import type { NextConfig } from "next";

// The browser only talks to this origin; /api/* is proxied to FastAPI so the
// session cookie stays first-party (see docs/architecture.md, decision D8).
const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
