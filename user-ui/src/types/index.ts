// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  user_name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  about: string;
  country: string;
  country_name: string;
  phone_number: string;
  postcode: string;
  address_line_1: string;
  address_line_2: string;
  town_city: string;
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

export interface ProductImage {
  id: number;
  image: string;
  alt_text: string;
  is_primary: boolean;
  ordering: number;
}

export interface Product {
  id: number;
  title: string;
  slug: string;
  description: string;
  category_name: string;
  category?: Category;
  price: string;
  discount_price: string | null;
  effective_price: string;
  image: string;
  images?: ProductImage[];
  in_stock: boolean;
  stock_quantity: number;
  created: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ── Basket ────────────────────────────────────────────────────────────────────
export interface BasketItem {
  product_id: number;
  title: string;
  slug: string;
  image: string | null;
  price: string;
  qty: number;
  line_total: string;
  stock_quantity: number;
}

export interface Basket {
  items: BasketItem[];
  total_items: number;
  subtotal: string;
}

// ── Orders ────────────────────────────────────────────────────────────────────
export interface OrderItem {
  id: number;
  product: number;
  product_title: string;
  price: string;
  quantity: number;
  line_total: string;
}

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "refunded";

export interface Order {
  id: number;
  order_number: string;
  order_key: string;
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

// ── Checkout form ─────────────────────────────────────────────────────────────
export interface CheckoutFormData {
  full_name: string;
  email: string;
  phone: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  postcode: string;
  country: string;
}
