import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  transpilePackages: ['@phosphor-icons/react'],
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://localhost:5000/socket.io/:path*',
      },
      {
        source: '/events/:path*',
        destination: 'http://localhost:5000/events/:path*',
      },
    ]
  },
}

export default nextConfig
