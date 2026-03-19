import api from "@/lib/api";
import type { AuthTokens, User, Product, Category, Order, AdminStats } from "@/types";

// Write payload types — prices are numbers when sending to the API
// (Django accepts both; the response always returns strings)
export interface ProductWritePayload {
  title: string;
  description?: string;
  category_id: number;
  price: number;
  discount_price?: number;
  stock_quantity: number;
  is_active: boolean;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthTokens>("/auth/token/", { email, password }),
  me: () => api.get<User>("/auth/me/"),
  logout: (refresh: string) => api.post("/auth/token/blacklist/", { refresh }),
};

export const statsApi = {
  get: () => api.get<AdminStats>("/admin/stats/"),
};

export const productsApi = {
  list: () => api.get<Product[]>("/admin/products/"),
  detail: (slug: string) => api.get<Product>(`/admin/products/${slug}/`),
  create: (data: ProductWritePayload) =>
    api.post<Product>("/admin/products/", data),
  update: (slug: string, data: Partial<ProductWritePayload>) =>
    api.patch<Product>(`/admin/products/${slug}/`, data),
  delete: (slug: string) => api.delete(`/admin/products/${slug}/`),
};

export const categoriesApi = {
  list: () => api.get<Category[]>("/admin/categories/"),
  create: (data: { name: string; description?: string; is_active?: boolean }) =>
    api.post<Category>("/admin/categories/", data),
  update: (slug: string, data: Partial<Category>) =>
    api.patch<Category>(`/admin/categories/${slug}/`, data),
  delete: (slug: string) => api.delete(`/admin/categories/${slug}/`),
};

export const ordersApi = {
  list: (params?: { status?: string; billing_status?: string }) =>
    api.get<Order[]>("/admin/orders/", { params }),
  detail: (orderNumber: string) => api.get<Order>(`/orders/${orderNumber}/`),
  updateStatus: (orderNumber: string, status: string) =>
    api.put<Order>(`/admin/orders/${orderNumber}/status/`, { status }),
  markPaid: (orderNumber: string) =>
    api.post<Order>(`/admin/orders/${orderNumber}/mark-paid/`),
};

export const usersApi = {
  list: (params?: { search?: string; is_active?: string }) =>
    api.get<User[]>("/admin/users/", { params }),
  detail: (id: number) => api.get<User>(`/admin/users/${id}/`),
  deactivate: (id: number) => api.post(`/admin/users/${id}/deactivate/`),
};
