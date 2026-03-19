"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

export default function AdminBootstrap({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchMe } = useAuthStore();
  useEffect(() => {
    if (isAuthenticated) fetchMe();
  }, [isAuthenticated, fetchMe]);
  return <>{children}</>;
}
