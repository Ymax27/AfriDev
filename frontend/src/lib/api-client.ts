import axios, { AxiosError, type AxiosRequestConfig } from "axios";

const UNSAFE_METHODS = new Set(["post", "put", "patch", "delete"]);

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
  withCredentials: true,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const method = (config.method ?? "get").toLowerCase();
  if (UNSAFE_METHODS.has(method)) {
    const csrf = readCookie("afridev_csrf");
    if (csrf) config.headers.set("X-CSRF-Token", csrf);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: { code?: string; message?: string; details?: unknown } }>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("afridev:unauthorized"));
    }
    const payload = error.response?.data?.error;
    const message =
      payload?.message ??
      (error.code === "ECONNABORTED" ? "Request timed out" : "Network error, please retry");
    return Promise.reject(
      new ApiError(
        message,
        error.response?.status ?? 0,
        payload?.code ?? "network_error",
        payload?.details,
      ),
    );
  },
);

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<T>(config);
  return response.data;
}

export function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}
