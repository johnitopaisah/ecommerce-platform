/**
 * Axios instance with JWT auto-refresh.
 *
 * - Server-side (SSR/SSG): uses INTERNAL_API_URL (http://api:8000/api/v1)
 *   so Next.js can reach Django directly inside the cluster.
 * - Client-side (browser): uses /api/v1 (relative) so the browser calls
 *   the same host it loaded from, and Next.js rewrites proxy it to Django.
 *
 * This means NO build-time URL is ever needed — works on any host.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  typeof window === "undefined"
    ? // Server-side: use internal cluster URL
      `${process.env.INTERNAL_API_URL || "http://api:8000"}/api/v1`
    : // Client-side: relative URL proxied by Next.js rewrites
      "/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
});

// ── Request interceptor — attach access token (client-side only) ──────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor — auto-refresh on 401 ───────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token!);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken =
        typeof window !== "undefined"
          ? localStorage.getItem("refresh_token")
          : null;

      if (!refreshToken) {
        isRefreshing = false;
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(
          `${process.env.INTERNAL_API_URL || "http://api:8000"}/api/v1/auth/token/refresh/`,
          { refresh: refreshToken }
        );

        const newAccess: string = data.access;
        localStorage.setItem("access_token", newAccess);
        if (data.refresh) localStorage.setItem("refresh_token", data.refresh);

        api.defaults.headers.common.Authorization = `Bearer ${newAccess}`;
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        processQueue(null, newAccess);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
