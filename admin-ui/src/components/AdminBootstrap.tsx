"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { usePermissionsStore } from "@/store/permissionsStore";

export default function AdminBootstrap({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchMe } = useAuthStore();
  const { fetchPermissions, clear: clearPermissions } = usePermissionsStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchMe();
      fetchPermissions();
    } else {
      clearPermissions();
    }
  }, [isAuthenticated, fetchMe, fetchPermissions, clearPermissions]);

  return <>{children}</>;
}
