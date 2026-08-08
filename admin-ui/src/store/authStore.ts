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
  _hasHydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  clearAuth: () => void;
  setHasHydrated: (value: boolean) => void;
  tryAdoptExistingSession: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      _hasHydrated: false,

      setHasHydrated: (value) => set({ _hasHydrated: value }),

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

      // Storefront (user-ui) and admin-ui share an origin, so a storefront
      // login's tokens ("access_token"/"refresh_token") sitting in
      // localStorage are readable here even though admin-ui normally keeps
      // its own separate "admin_access_token" pair. If someone is already
      // signed in on the storefront and turns out to be staff, adopt that
      // session instead of making them log in a second time — this is what
      // "click Admin Panel and just land in the dashboard" actually needs.
      // Reverts cleanly (no half-adopted state) if the token is missing,
      // invalid, or belongs to a non-staff account.
      tryAdoptExistingSession: async () => {
        if (typeof window === "undefined") return false;
        if (get().isAuthenticated) return true;

        const storefrontAccess = localStorage.getItem("access_token");
        const storefrontRefresh = localStorage.getItem("refresh_token");
        if (!storefrontAccess || !storefrontRefresh) return false;

        localStorage.setItem("admin_access_token", storefrontAccess);
        localStorage.setItem("admin_refresh_token", storefrontRefresh);
        set({ accessToken: storefrontAccess, refreshToken: storefrontRefresh });

        try {
          const { data } = await authApi.me();
          if (!data.is_staff) {
            get().clearAuth();
            return false;
          }
          set({ user: data, isAuthenticated: true });
          document.cookie = "admin_authenticated=1; path=/; max-age=604800; SameSite=Lax";
          return true;
        } catch {
          get().clearAuth();
          return false;
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
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
