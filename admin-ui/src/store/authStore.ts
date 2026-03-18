import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { authApi } from "@/lib/services";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      clearAuth: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("admin_access_token");
          localStorage.removeItem("admin_refresh_token");
          document.cookie = "admin_authenticated=; max-age=0; path=/";
        }
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { data } = await authApi.login(email, password);

          // Staff check happens after we have the token — fetch /me/
          if (typeof window !== "undefined") {
            localStorage.setItem("admin_access_token", data.access);
            localStorage.setItem("admin_refresh_token", data.refresh);
          }
          set({ accessToken: data.access, refreshToken: data.refresh });

          // Verify the user is staff
          const meRes = await authApi.me();
          if (!meRes.data.is_staff) {
            get().clearAuth();
            throw new Error("Access denied. Admin accounts only.");
          }

          set({ user: meRes.data, isAuthenticated: true });
          if (typeof window !== "undefined") {
            document.cookie = "admin_authenticated=1; path=/; max-age=604800; SameSite=Lax";
          }
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        const refresh = get().refreshToken;
        if (refresh) {
          try { await authApi.logout(refresh); } catch { /* ignore */ }
        }
        get().clearAuth();
      },

      fetchMe: async () => {
        try {
          const { data } = await authApi.me();
          if (!data.is_staff) { get().clearAuth(); return; }
          set({ user: data, isAuthenticated: true });
        } catch {
          get().clearAuth();
        }
      },
    }),
    {
      name: "admin-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        isAuthenticated: s.isAuthenticated,
      }),
    }
  )
);
