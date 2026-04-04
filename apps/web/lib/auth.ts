import { cookies } from "next/headers";

export const AUTH_TOKEN_COOKIE = "pharmahub_access_token";
export const AUTH_ROLE_COOKIE = "pharmahub_role";
export const AUTH_USERNAME_COOKIE = "pharmahub_username";
export const AUTH_EXPIRES_AT_COOKIE = "pharmahub_expires_at";

export type SessionUser = {
  id: number;
  username: string;
  role: "admin" | "viewer";
  is_system_account: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  expires_at: string;
  user: SessionUser;
};

function cookieOptions(expiresAt?: Date) {
  return {
    expires: expiresAt,
    httpOnly: false,
    path: "/",
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

export async function getAuthToken() {
  return (await cookies()).get(AUTH_TOKEN_COOKIE)?.value;
}

export async function getSessionSnapshot() {
  const jar = await cookies();
  const username = jar.get(AUTH_USERNAME_COOKIE)?.value;
  const role = jar.get(AUTH_ROLE_COOKIE)?.value as SessionUser["role"] | undefined;
  const expiresAt = jar.get(AUTH_EXPIRES_AT_COOKIE)?.value;

  if (!username || !role) {
    return null;
  }

  return { username, role, expiresAt };
}

export async function persistSession(login: LoginResponse) {
  const jar = await cookies();
  const expiresAt = new Date(login.expires_at);
  jar.set(AUTH_TOKEN_COOKIE, login.access_token, cookieOptions(expiresAt));
  jar.set(AUTH_USERNAME_COOKIE, login.user.username, cookieOptions(expiresAt));
  jar.set(AUTH_ROLE_COOKIE, login.user.role, cookieOptions(expiresAt));
  jar.set(AUTH_EXPIRES_AT_COOKIE, login.expires_at, cookieOptions(expiresAt));
}

export async function refreshSessionUser(user: SessionUser, expiresAt?: string) {
  const jar = await cookies();
  const nextExpiry = expiresAt ? new Date(expiresAt) : undefined;
  jar.set(AUTH_USERNAME_COOKIE, user.username, cookieOptions(nextExpiry));
  jar.set(AUTH_ROLE_COOKIE, user.role, cookieOptions(nextExpiry));
  if (expiresAt) {
    jar.set(AUTH_EXPIRES_AT_COOKIE, expiresAt, cookieOptions(nextExpiry));
  }
}

export async function clearSession() {
  const jar = await cookies();
  jar.delete(AUTH_TOKEN_COOKIE);
  jar.delete(AUTH_USERNAME_COOKIE);
  jar.delete(AUTH_ROLE_COOKIE);
  jar.delete(AUTH_EXPIRES_AT_COOKIE);
}
