import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { AUTH_TOKEN_COOKIE } from "./lib/auth";

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const isPublicRoute = pathname === "/login";

  if (!token && !isPublicRoute) {
    const loginUrl = new URL("/login", request.url);
    const nextValue = pathname + request.nextUrl.search;
    loginUrl.searchParams.set("next", nextValue || "/");
    return NextResponse.redirect(loginUrl);
  }

  if (token && isPublicRoute) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-pathname", pathname);

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
