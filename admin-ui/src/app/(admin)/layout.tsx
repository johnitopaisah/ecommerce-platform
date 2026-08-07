"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import Sidebar from "@/components/layout/Sidebar";

export default function AdminShellLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, _hasHydrated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Zustand's persisted isAuthenticated starts false for one render tick
    // before rehydrating from localStorage — redirecting on that first
    // render (before _hasHydrated flips true) kicked every logged-in admin
    // back to /login on any fresh page load, refresh, or direct URL open.
    if (_hasHydrated && !isAuthenticated) router.replace("/login");
  }, [_hasHydrated, isAuthenticated, router]);

  if (!_hasHydrated) return null;
  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
