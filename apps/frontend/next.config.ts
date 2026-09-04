import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    unoptimized: true,
  },
  transpilePackages: ["@phosphor-icons/react"],
  allowedDevOrigins: ["gentile-balmy-unstirred.ngrok-free.dev"],
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    // Same-origin proxy so browser clients (incl. EventSource, which sends no
    // auth headers) never depend on build-time NEXT_PUBLIC_API_URL. In docker
    // BACKEND_URL points at the backend container; locally it is the dev API.
    const backend = process.env.BACKEND_URL || "http://localhost:5000";
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
      { source: "/events/:path*", destination: `${backend}/events/:path*` },
    ];
  },
};

export default nextConfig;
