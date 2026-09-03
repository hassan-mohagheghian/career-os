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
};

export default nextConfig;
