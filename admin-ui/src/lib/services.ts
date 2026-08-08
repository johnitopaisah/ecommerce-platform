import api from "@/lib/api";
import type {
  AuthTokens, User, Product, Category, Order, AdminStats, Review, Coupon,
  TeamMember, Role, Permission, RoleGrant, RoleGrantRequest, AuditLogEntry,
} from "@/types";

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
  uploadImage: (slug: string, file: File) => {
    const form = new FormData();
    form.append("image", file);
    form.append("is_primary", "true");
    return api.post(`/admin/products/${slug}/images/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteImage: (slug: string, imageId: number) =>
    api.delete(`/admin/products/${slug}/images/${imageId}/`),
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

// Shared detail/deactivate — works for either a customer or a team member,
// the account itself doesn't differ, only which *list* it shows up in.
export const usersApi = {
  detail: (id: number) => api.get<User>(`/admin/users/${id}/`),
  deactivate: (id: number) => api.post(`/admin/users/${id}/deactivate/`),
};

export const customersApi = {
  list: (params?: { search?: string; is_active?: string }) =>
    api.get<User[]>("/admin/customers/", { params }),
};

export interface TeamMemberCreatePayload {
  email: string;
  user_name: string;
  first_name?: string;
  last_name?: string;
  initial_group_id?: number;
  duration_hours?: number;
}

export const teamApi = {
  list: (params?: { search?: string; is_active?: string }) =>
    api.get<TeamMember[]>("/admin/team/", { params }),
  create: (data: TeamMemberCreatePayload) => api.post<TeamMember>("/admin/team/", data),
};

export const rolesApi = {
  list: () => api.get<Role[]>("/rbac/roles/"),
  detail: (id: number) => api.get<Role>(`/rbac/roles/${id}/`),
  create: (data: { name: string; permission_codenames: string[] }) =>
    api.post<Role>("/rbac/roles/", data),
  update: (id: number, data: Partial<{ name: string; permission_codenames: string[] }>) =>
    api.patch<Role>(`/rbac/roles/${id}/`, data),
  delete: (id: number) => api.delete(`/rbac/roles/${id}/`),
  permissions: () => api.get<Permission[]>("/rbac/permissions/"),
};

export const rbacApi = {
  myPermissions: () => api.get<{ is_superuser: boolean; permissions: string[] }>("/rbac/me/permissions/"),
  myGrants: () => api.get<RoleGrant[]>("/rbac/me/grants/"),

  myRequests: () => api.get<RoleGrantRequest[]>("/rbac/requests/"),
  requestRole: (data: { group_id: number; duration_hours?: number | null; justification: string }) =>
    api.post<RoleGrantRequest>("/rbac/requests/", data),
  cancelRequest: (id: number) => api.post<RoleGrantRequest>(`/rbac/requests/${id}/cancel/`),

  pendingRequests: () => api.get<RoleGrantRequest[]>("/rbac/requests/pending/"),
  approveRequest: (id: number, reason?: string) =>
    api.post<RoleGrantRequest>(`/rbac/requests/${id}/approve/`, { reason: reason || "" }),
  denyRequest: (id: number, reason?: string) =>
    api.post<RoleGrantRequest>(`/rbac/requests/${id}/deny/`, { reason: reason || "" }),

  grants: (userId?: number) =>
    api.get<RoleGrant[]>("/rbac/grants/", { params: userId ? { user: userId } : undefined }),
  revokeGrant: (id: number) => api.post<RoleGrant>(`/rbac/grants/${id}/revoke/`),
};

export const auditLogApi = {
  list: (params?: { actor?: number; action?: string; outcome?: string; search?: string }) =>
    api.get<AuditLogEntry[]>("/admin/audit-log/", { params }),
};

export const reviewsApi = {
  list: (isApproved?: boolean) =>
    api.get<Review[]>("/admin/reviews/", {
      params: isApproved === undefined ? undefined : { is_approved: isApproved },
    }),
  approve: (id: number) => api.patch<Review>(`/admin/reviews/${id}/`, { is_approved: true }),
  reject: (id: number) => api.patch<Review>(`/admin/reviews/${id}/`, { is_approved: false }),
  delete: (id: number) => api.delete(`/admin/reviews/${id}/`),
};

export interface CouponWritePayload {
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  is_active?: boolean;
  valid_from?: string | null;
  valid_until?: string | null;
  min_order_value?: number | null;
  usage_limit?: number | null;
}

export const couponsApi = {
  list: () => api.get<Coupon[]>("/admin/coupons/"),
  create: (data: CouponWritePayload) => api.post<Coupon>("/admin/coupons/", data),
  update: (id: number, data: Partial<CouponWritePayload>) =>
    api.patch<Coupon>(`/admin/coupons/${id}/`, data),
  delete: (id: number) => api.delete(`/admin/coupons/${id}/`),
};
