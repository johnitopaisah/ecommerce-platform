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
  setTokens: (access: string, refresh: string) => void;
  clearAuth: () => void;
  setHasHydrated: (value: boolean) => void;
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

      setTokens: (access, refresh) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", access);
          localStorage.setItem("refresh_token", refresh);
        }
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
      },

      clearAuth: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          // Clear the middleware cookie too
          document.cookie = "is_authenticated=; max-age=0; path=/";
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { data } = await authApi.login(email, password);
          get().setTokens(data.access, data.refresh);
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        const refresh = get().refreshToken;
        if (refresh) {
          try {
            await authApi.logout(refresh);
          } catch {
            // ignore
          }
        }
        get().clearAuth();
      },

      fetchMe: async () => {
        try {
          const { data } = await authApi.me();
          set({ user: data, isAuthenticated: true });
        } catch {
          get().clearAuth();
        }
      },
    }),
    {
      name: "auth-storage",
      // Persist user too so the sidebar shows name immediately on hydration
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
