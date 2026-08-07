// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  user_name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  is_staff: boolean;
  created: string;
  updated: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// ── Store ─────────────────────────────────────────────────────────────────────
export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  product_count: number;
}

export interface Product {
  id: number;
  title: string;
  slug: string;
  description: string;
  category: Category;
  category_id?: number;
  price: string;
  discount_price: string | null;
  effective_price: string;
  image: string;
  stock_quantity: number;
  in_stock: boolean;
  is_active: boolean;
  created_by: string;
  created: string;
  updated: string;
}

// ── Orders ────────────────────────────────────────────────────────────────────
export type OrderStatus =
  | "pending" | "confirmed" | "processing"
  | "shipped" | "delivered" | "cancelled" | "refunded";

export interface OrderItem {
  id: number;
  product: number;
  product_title: string;
  price: string;
  quantity: number;
  line_total: string;
}

export interface Order {
  id: number;
  order_number: string;
  user: number;
  status: OrderStatus;
  status_display: string;
  total_paid: string;
  billing_status: boolean;
  full_name: string;
  email: string;
  phone: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  postcode: string;
  country: string;
  items: OrderItem[];
  created: string;
  updated: string;
}

// ── Reviews ───────────────────────────────────────────────────────────────────
export interface Review {
  id: number;
  product_title: string;
  product_slug: string;
  reviewer_email: string;
  rating: number;
  title: string;
  comment: string;
  verified_purchase: boolean;
  is_approved: boolean;
  created: string;
}

// ── Coupons ───────────────────────────────────────────────────────────────────
export type DiscountType = "percentage" | "fixed";

export interface Coupon {
  id: number;
  code: string;
  discount_type: DiscountType;
  discount_value: string;
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
  min_order_value: string | null;
  usage_limit: number | null;
  times_used: number;
  created: string;
  updated: string;
}

// ── Stats ─────────────────────────────────────────────────────────────────────
export interface AdminStats {
  users: { total: number; active: number; new_today: number };
  products: { total_active: number; low_stock: number; out_of_stock: number };
  orders: { total: number; today: number; pending: number };
  revenue: {
    total: string;
    last_30_days: string;
    confirmed_total: string;
  };
}
