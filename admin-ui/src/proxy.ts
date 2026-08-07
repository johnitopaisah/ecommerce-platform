import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC = ["/login"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isLoggedIn = request.cookies.has("admin_authenticated");
  const isPublic = PUBLIC.some((p) => pathname.startsWith(p));

  // request.nextUrl.clone() (not `new URL(path, request.url)`) is required
  // here — with basePath: "/admin-panel" set, request.nextUrl.pathname is
  // already basePath-stripped for route matching, so building a fresh URL
  // from it drops the prefix entirely. Confirmed live: unauthenticated
  // visits to /admin-panel/dashboard were redirecting to bare
  // /login?next=/dashboard (no /admin-panel prefix), landing on user-ui's
  // storefront login instead of admin-ui's. .clone() preserves basePath.

  // Redirect unauthenticated users to login
  if (!isPublic && !isLoggedIn) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${pathname}`;
    return NextResponse.redirect(url);
  }

  // Redirect authenticated users away from login
  if (isPublic && isLoggedIn) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|placeholder.svg).*)"],
};
