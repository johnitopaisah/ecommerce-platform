import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/account", "/checkout"];
const AUTH_ONLY = ["/login", "/register"];
// These pages must be accessible to everyone regardless of auth state
const PUBLIC_ALWAYS = ["/activated", "/activation-failed", "/reset-password"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Never intercept these routes
  if (PUBLIC_ALWAYS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const isLoggedIn = request.cookies.has("is_authenticated");
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p));
  const isAuthOnly = AUTH_ONLY.some((p) => pathname.startsWith(p));

  if (isProtected && !isLoggedIn) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthOnly && isLoggedIn) {
    return NextResponse.redirect(new URL("/account", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/account/:path*",
    "/checkout/:path*",
    "/login",
    "/register",
    "/activated",
    "/activation-failed",
  ],
};
