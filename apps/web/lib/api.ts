import { getAuthToken } from "./auth";

export const API_BASE_URL = process.env.INTERNAL_API_BASE_URL ?? "http://api:8000";

type FetchResult<T> = {
  ok: boolean;
  status: number;
  url: string;
  data: T | null;
  error: string | null;
};

function buildUrl(path: string, query?: Record<string, string | undefined>) {
  const url = new URL(path, API_BASE_URL);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value && value.trim().length > 0) {
        url.searchParams.set(key, value.trim());
      }
    }
  }
  return url.toString();
}

type FetchOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
};

export async function fetchApi<T>(
  path: string,
  query?: Record<string, string | undefined>,
  options?: FetchOptions,
): Promise<FetchResult<T>> {
  const url = buildUrl(path, query);
  try {
    const token = options?.token === null ? null : (options?.token ?? (await getAuthToken()) ?? null);
    const response = await fetch(url, {
      method: options?.method ?? "GET",
      cache: "no-store",
      headers: {
        ...(options?.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(options?.body ? { body: JSON.stringify(options.body) } : {}),
    });
    const text = await response.text();
    const payload = text ? JSON.parse(text) : null;

    if (!response.ok) {
      const message =
        payload && typeof payload === "object" && "detail" in payload
          ? String((payload as { detail?: unknown }).detail ?? "API request failed")
          : "API request failed";
      return { ok: false, status: response.status, url, data: payload as T | null, error: message };
    }

    return { ok: true, status: response.status, url, data: payload as T, error: null };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      url,
      data: null,
      error: error instanceof Error ? error.message : "Unexpected request error",
    };
  }
}
