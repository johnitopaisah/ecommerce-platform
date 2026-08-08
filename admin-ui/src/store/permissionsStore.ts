import { create } from "zustand";
import { rbacApi } from "@/lib/services";

interface PermissionsState {
  permissions: string[];
  isSuperuser: boolean;
  loaded: boolean;
  fetchPermissions: () => Promise<void>;
  hasPermission: (codename: string) => boolean;
  clear: () => void;
}

export const usePermissionsStore = create<PermissionsState>()((set, get) => ({
  permissions: [],
  isSuperuser: false,
  loaded: false,

  fetchPermissions: async () => {
    try {
      const { data } = await rbacApi.myPermissions();
      set({ permissions: data.permissions, isSuperuser: data.is_superuser, loaded: true });
    } catch {
      set({ permissions: [], isSuperuser: false, loaded: true });
    }
  },

  // Mirrors the backend's own rule exactly: superuser bypasses everything,
  // otherwise the codename must be in the resolved effective-permissions
  // set. Used purely for UI affordance (show/hide a button) — the real
  // security boundary is always server-side (apps.rbac.permissions).
  hasPermission: (codename) => {
    const state = get();
    return state.isSuperuser || state.permissions.includes(codename);
  },

  clear: () => set({ permissions: [], isSuperuser: false, loaded: false }),
}));
