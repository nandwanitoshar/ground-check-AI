import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.BACKEND_URL ||
      "http://127.0.0.1:8000";
    const cleanUrl = backendUrl.replace(/\/+$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${cleanUrl}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${cleanUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
