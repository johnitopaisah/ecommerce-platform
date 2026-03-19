import api from "./api";
import type {
  AuthTokens,
  User,
  Category,
  Product,
  PaginatedResponse,
  Basket,
  Order,
  CheckoutFormData,
} from "@/types";

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthTokens>("/auth/token/", { email, password }),

  refresh: (refresh: string) =>
    api.post<{ access: string; refresh: string }>("/auth/token/refresh/", {
      refresh,
    }),

  logout: (refresh: string) =>
    api.post("/auth/token/blacklist/", { refresh }),

  register: (data: {
    email: string;
    user_name: string;
    first_name: string;
    last_name: string;
    password: string;
    password2: string;
  }) => api.post("/auth/register/", data),

  me: () => api.get<User>("/auth/me/"),

  updateMe: (data: Partial<User>) => api.patch<User>("/auth/me/", data),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    new_password2: string;
  }) => api.post("/auth/me/change-password/", data),

  passwordReset: (email: string) =>
    api.post("/auth/password-reset/", { email }),

  passwordResetConfirm: (data: {
    uid: string;
    token: string;
    new_password: string;
    new_password2: string;
  }) => api.post("/auth/password-reset/confirm/", data),
};

// ── Products ──────────────────────────────────────────────────────────────────
export const productsApi = {
  list: (params?: {
    category?: string;
    search?: string;
    min_price?: number;
    max_price?: number;
    in_stock?: boolean;
    ordering?: string;
    page?: number;
    page_size?: number;
  }) => api.get<PaginatedResponse<Product>>("/products/", { params }),

  detail: (slug: string) => api.get<Product>(`/products/${slug}/`),
};

// ── Categories ────────────────────────────────────────────────────────────────
export const categoriesApi = {
  list: () => api.get<Category[]>("/categories/"),

  detail: (slug: string) => api.get<Category>(`/categories/${slug}/`),

  products: (
    slug: string,
    params?: { ordering?: string; page?: number }
  ) =>
    api.get<PaginatedResponse<Product>>(`/categories/${slug}/products/`, {
      params,
    }),
};

// ── Basket ────────────────────────────────────────────────────────────────────
export const basketApi = {
  get: () => api.get<Basket>("/basket/"),

  add: (product_id: number, qty: number) =>
    api.post<Basket>("/basket/items/", { product_id, qty }),

  update: (product_id: number, qty: number) =>
    api.put<Basket>(`/basket/items/${product_id}/`, { qty }),

  remove: (product_id: number) =>
    api.delete<Basket>(`/basket/items/${product_id}/remove/`),

  clear: () => api.delete<void>("/basket/"),

  merge: () => api.post<Basket>("/basket/merge/"),
};

// ── Orders ────────────────────────────────────────────────────────────────────
export const ordersApi = {
  list: () => api.get<Order[]>("/orders/"),

  detail: (orderNumber: string) =>
    api.get<Order>(`/orders/${orderNumber}/`),

  create: (data: CheckoutFormData & { order_key: string }) =>
    api.post<Order>("/orders/", data),

  cancel: (orderNumber: string) =>
    api.post<Order>(`/orders/${orderNumber}/cancel/`),
};

// ── Payment ───────────────────────────────────────────────────────────────────
export const paymentApi = {
  createIntent: () =>
    api.post<{
      client_secret: string;
      payment_intent_id: string;
      amount: string;
      currency: string;
    }>("/payment/create-intent/"),

  status: (orderNumber: string) =>
    api.get(`/payment/${orderNumber}/`),
};
