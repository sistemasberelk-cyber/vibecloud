import { NextResponse } from 'next/server';

export function middleware(request) {
  const { pathname } = request.nextUrl;

  // Check the is_onboarded cookie
  const isOnboardedCookie = request.cookies.get('is_onboarded');
  
  if (isOnboardedCookie && isOnboardedCookie.value === 'false') {
    return NextResponse.redirect(new URL('/onboarding', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|login|onboarding).*)',
  ],
};
