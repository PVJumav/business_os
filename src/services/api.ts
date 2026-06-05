import { API_BASE_URL } from "@/lib/constants";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>;
}

export function apiUrl(endpoint: string, params?: Record<string, string | number>) {
  if (/^https?:\/\//i.test(endpoint)) return endpoint;
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))
    );
    url += `?${qs.toString()}`;
  }
  return url;
}

export function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export function errorMessageFromPayload(payload: unknown, fallback = "Request failed") {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown; message?: unknown; error?: unknown }).detail
    ?? (payload as { message?: unknown }).message
    ?? (payload as { error?: unknown }).error;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String((item as { msg: unknown }).msg);
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return fallback;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  const url = apiUrl(endpoint, params);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  let res: Response;
  try {
    res = await fetchWithRetry(url, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...fetchOptions.headers,
      },
      ...fetchOptions,
    });
  } catch (error) {
    throw new Error(
      error instanceof Error && error.message
        ? `Unable to reach the BusinessOS API. The server may still be waking up. Please try again in a moment.`
        : "Unable to reach the BusinessOS API."
    );
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorMessageFromPayload(error, res.statusText || "Request failed"));
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

async function fetchWithRetry(url: string, options: RequestInit, attempts = 3): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fetch(url, options);
    } catch (error) {
      lastError = error;
      if (attempt === attempts) break;
      await new Promise((resolve) => setTimeout(resolve, attempt * 3000));
    }
  }
  throw lastError;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { method: "GET", ...options }),

  post: <T>(endpoint: string, body: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { method: "POST", body: JSON.stringify(body), ...options }),

  put: <T>(endpoint: string, body: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { method: "PUT", body: JSON.stringify(body), ...options }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { method: "DELETE", ...options }),

  upload: async <T>(endpoint: string, body: FormData, params?: Record<string, string | number>) => {
    const res = await fetchWithRetry(apiUrl(endpoint, params), {
      method: "POST",
      headers: authHeaders(),
      body,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorMessageFromPayload(error, res.statusText || "Upload failed"));
    }
    return res.json() as Promise<T>;
  },
};
