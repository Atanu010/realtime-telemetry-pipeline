import { API_BASE } from "./config";

// Base API endpoint - works in development proxy and standalone production
const BASE = API_BASE ? `${API_BASE}/api` : "/api";

export const OPERATOR_TOKEN_KEY = "streampulse_operator_token";
export const OPERATOR_NAME_KEY = "streampulse_operator_name";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`request failed with ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

type JsonBody = unknown;

export function getStoredToken(): string | null {
  return localStorage.getItem(OPERATOR_TOKEN_KEY);
}

export function setStoredToken(token: string, name: string = "Atanu"): void {
  localStorage.setItem(OPERATOR_TOKEN_KEY, token);
  localStorage.setItem(OPERATOR_NAME_KEY, name);
}

export function clearStoredToken(): void {
  localStorage.removeItem(OPERATOR_TOKEN_KEY);
  localStorage.removeItem(OPERATOR_NAME_KEY);
  window.dispatchEvent(new Event("operator-auth-changed"));
}

export function getStoredOperatorName(): string {
  return localStorage.getItem(OPERATOR_NAME_KEY) || "Atanu";
}

async function request<T>(method: string, path: string, body?: JsonBody): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (res.status === 401) {
    // If an authenticated endpoint returns 401, clear stored auth
    if (path !== "/auth/login") {
      clearStoredToken();
    }
    const errBody = await res.json().catch(() => null);
    throw new ApiError(res.status, errBody);
  }

  if (!res.ok) {
    const errBody = await res.json().catch(() => null);
    throw new ApiError(res.status, errBody);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiGet = <T>(path: string) => request<T>("GET", path);
export const apiPost = <T>(path: string, body?: JsonBody) => request<T>("POST", path, body ?? null);
export const apiPut = <T>(path: string, body?: JsonBody) => request<T>("PUT", path, body ?? null);
export const apiPatch = <T>(path: string, body?: JsonBody) => request<T>("PATCH", path, body ?? null);
export const apiDelete = <T>(path: string) => request<T>("DELETE", path);

export async function loginOperator(key: string): Promise<{ token: string; operator: { name: string; role: string } }> {
  const data = await apiPost<{ token: string; operator: { name: string; role: string } }>("/auth/login", { key });
  setStoredToken(data.token, data.operator.name);
  window.dispatchEvent(new Event("operator-auth-changed"));
  return data;
}

export async function verifyOperator(): Promise<{ name: string; role: string } | null> {
  try {
    return await apiGet<{ name: string; role: string }>("/auth/me");
  } catch {
    clearStoredToken();
    return null;
  }
}
