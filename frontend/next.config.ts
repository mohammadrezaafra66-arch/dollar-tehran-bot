import type { NextConfig } from "next";

const apiTarget = process.env.PANEL_API_URL ?? "http://localhost:8100";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiTarget}/api/:path*` }];
  },
};

export default nextConfig;
