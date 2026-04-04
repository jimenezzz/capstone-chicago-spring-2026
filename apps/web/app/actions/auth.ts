"use server";

import { redirect } from "next/navigation";

import { LoginResponse, SessionUser, clearSession, persistSession, refreshSessionUser } from "../../lib/auth";
import { fetchApi } from "../../lib/api";

function messageUrl(path: string, key: string, value: string) {
  const url = new URL(path, "http://local");
  url.searchParams.set(key, value);
  return `${url.pathname}?${url.searchParams.toString()}`;
}

export async function loginAction(formData: FormData) {
  const username = String(formData.get("username") ?? "");
  const password = String(formData.get("password") ?? "");
  const next = String(formData.get("next") ?? "/");

  const response = await fetchApi<LoginResponse>("/auth/login", undefined, {
    method: "POST",
    body: { username, password },
    token: null,
  });

  if (!response.ok || !response.data) {
    const url = new URL("/login", "http://local");
    url.searchParams.set("error", response.error ?? "Unable to log in");
    url.searchParams.set("next", next.startsWith("/") ? next : "/");
    redirect(`${url.pathname}?${url.searchParams.toString()}`);
  }

  await persistSession(response.data);
  redirect(next.startsWith("/") ? next : "/");
}

export async function logoutAction() {
  await clearSession();
  redirect("/login");
}

export async function updateAccountAction(formData: FormData) {
  const currentPassword = String(formData.get("current_password") ?? "");
  const username = String(formData.get("username") ?? "").trim();
  const newPassword = String(formData.get("new_password") ?? "").trim();

  const body: Record<string, string> = { current_password: currentPassword };
  if (username) {
    body.username = username;
  }
  if (newPassword) {
    body.new_password = newPassword;
  }

  const response = await fetchApi<SessionUser>("/auth/me", undefined, {
    method: "PATCH",
    body,
  });

  if (!response.ok || !response.data) {
    redirect(messageUrl("/account", "error", response.error ?? "Unable to update account"));
  }

  await refreshSessionUser(response.data);
  redirect(messageUrl("/account", "success", "Account updated"));
}

export async function createUserAction(formData: FormData) {
  const username = String(formData.get("username") ?? "");
  const password = String(formData.get("password") ?? "");
  const role = String(formData.get("role") ?? "viewer");

  const response = await fetchApi<SessionUser>("/admin/users", undefined, {
    method: "POST",
    body: { username, password, role },
  });

  if (!response.ok) {
    redirect(messageUrl("/admin", "error", response.error ?? "Unable to create user"));
  }

  redirect(messageUrl("/admin", "success", "User created"));
}

export async function deleteUserAction(formData: FormData) {
  const userId = Number(String(formData.get("user_id") ?? "0"));

  const response = await fetchApi<null>(`/admin/users/${userId}`, undefined, {
    method: "DELETE",
  });

  if (!response.ok) {
    redirect(messageUrl("/admin", "error", response.error ?? "Unable to delete user"));
  }

  redirect(messageUrl("/admin", "success", "User deleted"));
}
