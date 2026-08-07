import { create } from "zustand";
import type { Basket } from "@/types";
import { basketApi } from "@/lib/services";

interface BasketState {
  basket: Basket;
  isLoading: boolean;
  couponLoading: boolean;
  fetchBasket: () => Promise<void>;
  addItem: (product_id: number, qty: number) => Promise<void>;
  updateItem: (product_id: number, qty: number) => Promise<void>;
  removeItem: (product_id: number) => Promise<void>;
  clearBasket: () => Promise<void>;
  mergeBasket: () => Promise<void>;
  applyCoupon: (code: string) => Promise<string | null>;
  removeCoupon: () => Promise<void>;
}

const emptyBasket: Basket = {
  items: [], total_items: 0, subtotal: "0.00",
  coupon_code: null, coupon_error: null, discount_amount: "0.00", total: "0.00",
};

export const useBasketStore = create<BasketState>()((set) => ({
  basket: emptyBasket,
  isLoading: false,
  couponLoading: false,

  fetchBasket: async () => {
    set({ isLoading: true });
    try {
      const { data } = await basketApi.get();
      set({ basket: data });
    } catch {
      set({ basket: emptyBasket });
    } finally {
      set({ isLoading: false });
    }
  },

  addItem: async (product_id, qty) => {
    set({ isLoading: true });
    try {
      const { data } = await basketApi.add(product_id, qty);
      set({ basket: data });
    } finally {
      set({ isLoading: false });
    }
  },

  updateItem: async (product_id, qty) => {
    set({ isLoading: true });
    try {
      const { data } = await basketApi.update(product_id, qty);
      set({ basket: data });
    } finally {
      set({ isLoading: false });
    }
  },

  removeItem: async (product_id) => {
    set({ isLoading: true });
    try {
      const { data } = await basketApi.remove(product_id);
      set({ basket: data });
    } finally {
      set({ isLoading: false });
    }
  },

  clearBasket: async () => {
    set({ isLoading: true });
    try {
      await basketApi.clear();
      set({ basket: emptyBasket });
    } finally {
      set({ isLoading: false });
    }
  },

  mergeBasket: async () => {
    try {
      const { data } = await basketApi.merge();
      set({ basket: data });
    } catch {
      // Non-critical
    }
  },

  // Returns an error message on failure (for inline display), null on success.
  applyCoupon: async (code) => {
    set({ couponLoading: true });
    try {
      const { data } = await basketApi.applyCoupon(code);
      set({ basket: data });
      return null;
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      return e?.response?.data?.detail || "Could not apply coupon.";
    } finally {
      set({ couponLoading: false });
    }
  },

  removeCoupon: async () => {
    set({ couponLoading: true });
    try {
      const { data } = await basketApi.removeCoupon();
      set({ basket: data });
    } finally {
      set({ couponLoading: false });
    }
  },
}));
