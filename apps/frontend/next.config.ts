import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:5000";

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  transpilePackages: ["@phosphor-icons/react"],
  allowedDevOrigins: ["gentile-balmy-unstirred.ngrok-free.dev"],
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: "/socket.io/:path*",
        destination: `${BACKEND_URL}/socket.io/:path*`,
      },
      {
        source: "/events/:path*",
        destination: `${BACKEND_URL}/events/:path*`,
      },
    ];
  },
};

export default nextConfig;
