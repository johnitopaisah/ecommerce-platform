/**
 * Axios instance with JWT auto-refresh.
 *
 * - Server-side: uses INTERNAL_API_URL (http://api:8000/api/v1)
 * - Client-side: uses /api/v1 (relative, proxied by Next.js rewrites)
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  typeof window === "undefined"
    ? `${process.env.INTERNAL_API_URL || "http://api:8000"}/api/v1`
    : "/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach access token on every request (client-side only)
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("admin_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: (t: string) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const orig = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !orig._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => failedQueue.push({ resolve, reject }))
          .then((token) => { orig.headers.Authorization = `Bearer ${token}`; return api(orig); })
          .catch(Promise.reject);
      }
      orig._retry = true;
      isRefreshing = true;
      const refresh = typeof window !== "undefined"
        ? localStorage.getItem("admin_refresh_token")
        : null;
      if (!refresh) {
        isRefreshing = false;
        if (typeof window !== "undefined") {
          localStorage.removeItem("admin_access_token");
          localStorage.removeItem("admin_refresh_token");
          window.location.href = "/admin-panel/login";
        }
        return Promise.reject(error);
      }
      try {
        const { data } = await axios.post(
          `${process.env.INTERNAL_API_URL || "http://api:8000"}/api/v1/auth/token/refresh/`,
          { refresh }
        );
        localStorage.setItem("admin_access_token", data.access);
        if (data.refresh) localStorage.setItem("admin_refresh_token", data.refresh);
        api.defaults.headers.common.Authorization = `Bearer ${data.access}`;
        orig.headers.Authorization = `Bearer ${data.access}`;
        processQueue(null, data.access);
        return api(orig);
      } catch (e) {
        processQueue(e, null);
        localStorage.removeItem("admin_access_token");
        localStorage.removeItem("admin_refresh_token");
        if (typeof window !== "undefined") window.location.href = "/admin-panel/login";
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
