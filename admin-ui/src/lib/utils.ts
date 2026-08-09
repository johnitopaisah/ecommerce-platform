import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: string | number): string {
  const num = typeof price === "string" ? parseFloat(price) : price;
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(num);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

export function getOrderStatusColor(status: string): string {
  const map: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
    confirmed: "bg-blue-100 text-blue-800 border-blue-200",
    processing: "bg-purple-100 text-purple-800 border-purple-200",
    shipped: "bg-indigo-100 text-indigo-800 border-indigo-200",
    delivered: "bg-green-100 text-green-800 border-green-200",
    cancelled: "bg-red-100 text-red-800 border-red-200",
    refunded: "bg-gray-100 text-gray-800 border-gray-200",
  };
  return map[status] ?? "bg-gray-100 text-gray-800 border-gray-200";
}

/** "3h 20m", "2d", "Expires soon", "Expired" — for time-bounded role grants. */
export function formatTimeUntil(dateStr: string): string {
  const diffMs = new Date(dateStr).getTime() - Date.now();
  if (diffMs <= 0) return "Expired";

  const minutes = Math.floor(diffMs / 60000);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const mins = minutes % 60;

  if (days > 0) return `${days}d${hours > 0 ? ` ${hours}h` : ""}`;
  if (hours > 0) return `${hours}h${mins > 0 ? ` ${mins}m` : ""}`;
  if (mins > 0) return `${mins}m`;
  return "Expires soon";
}

/**
 * Pulls a human-readable message out of an Axios error from the API.
 * The backend's global exception handler (apps.core.exceptions) always
 * shapes 400s as {error: "bad_request", detail: "...", errors: {field:
 * [...]}} — `detail` is already the right message to show; grabbing the
 * first object value instead (as several call sites used to) surfaces the
 * literal string "bad_request" rather than the actual reason.
 */
export function extractApiError(err: unknown, fallback = "Something went wrong."): string {
  const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
  if (!data) return fallback;
  if (typeof data.detail === "string" && data.detail) return data.detail;
  const errors = data.errors as Record<string, string[] | string> | undefined;
  if (errors) {
    const first = Object.values(errors)[0];
    if (first) return Array.isArray(first) ? first[0] : first;
  }
  return fallback;
}

export function getImageUrl(path: string | null | undefined): string {
  if (!path) return "/placeholder.svg";
  if (path.startsWith("http")) return path;
  // Relative paths (e.g. /media/products/x.jpg) resolve against whatever
  // host the page was loaded from — /media/* is proxied to Django the same
  // way /api/* is (see next.config.ts rewrites / the ingress routing in
  // k8s/ingress). No absolute base URL needed.
  return path;
}
