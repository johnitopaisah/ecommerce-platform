"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";

export default function AppBootstrap({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, fetchMe, clearAuth, _hasHydrated, accessToken } = useAuthStore();
  const { fetchBasket } = useBasketStore();

  useEffect(() => {
    if (!_hasHydrated) return;

    if (isAuthenticated && accessToken) {
      // Verify the stored token is still valid by fetching the user profile.
      // If the token is stale (e.g. after password reset), fetchMe calls
      // clearAuth internally which resets isAuthenticated to false.
      fetchMe();
    }

    // Always fetch basket (works for both guests and authenticated users)
    fetchBasket();
  }, [_hasHydrated]);

  return <>{children}</>;
}
