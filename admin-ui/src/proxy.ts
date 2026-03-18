import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC = ["/login"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isLoggedIn = request.cookies.has("admin_authenticated");
  const isPublic = PUBLIC.some((p) => pathname.startsWith(p));

  // Redirect unauthenticated users to login
  if (!isPublic && !isLoggedIn) {
    return NextResponse.redirect(new URL(`/login?next=${pathname}`, request.url));
  }

  // Redirect authenticated users away from login
  if (isPublic && isLoggedIn) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|placeholder.svg).*)"],
};
