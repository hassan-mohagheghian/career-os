import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:5000"

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (
    pathname.startsWith("/api/") ||
    pathname.startsWith("/socket.io/")
  ) {
    const url = new URL(pathname + request.nextUrl.search, BACKEND_URL)
    return NextResponse.rewrite(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/api/:path*", "/socket.io/:path*"],
}
