"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";

export default function AppBootstrap({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchMe, _hasHydrated } = useAuthStore();
  const { fetchBasket } = useBasketStore();

  useEffect(() => {
    if (!_hasHydrated) return;
    if (isAuthenticated) {
      fetchMe();
    }
    fetchBasket();
  }, [_hasHydrated, isAuthenticated, fetchMe, fetchBasket]);

  return <>{children}</>;
}
