"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";
import { useWishlistStore } from "@/store/wishlistStore";

export default function AppBootstrap({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchMe, _hasHydrated } = useAuthStore();
  const { fetchBasket } = useBasketStore();
  const { fetchWishlist, clear: clearWishlist } = useWishlistStore();

  useEffect(() => {
    if (!_hasHydrated) return;
    if (isAuthenticated) {
      fetchMe();
      fetchWishlist();
    } else {
      // Wishlist is fully user-scoped (unlike basket, which has an
      // anonymous session concept server-side) — nothing resets it for us
      // on logout, so clear it client-side or the next signed-out visitor
      // on this browser would see the previous user's hearts.
      clearWishlist();
    }
    fetchBasket();
  }, [_hasHydrated, isAuthenticated, fetchMe, fetchBasket, fetchWishlist, clearWishlist]);

  return <>{children}</>;
}
