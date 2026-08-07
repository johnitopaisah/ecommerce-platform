import { create } from "zustand";
import type { WishlistItem } from "@/types";
import { wishlistApi } from "@/lib/services";

interface WishlistState {
  items: WishlistItem[];
  slugs: Set<string>;
  isLoading: boolean;
  fetchWishlist: () => Promise<void>;
  toggle: (productSlug: string) => Promise<void>;
  isWishlisted: (productSlug: string) => boolean;
  clear: () => void;
}

export const useWishlistStore = create<WishlistState>()((set, get) => ({
  items: [],
  slugs: new Set(),
  isLoading: false,

  fetchWishlist: async () => {
    set({ isLoading: true });
    try {
      const { data } = await wishlistApi.list();
      set({ items: data, slugs: new Set(data.map((i) => i.product_slug)) });
    } catch {
      set({ items: [], slugs: new Set() });
    } finally {
      set({ isLoading: false });
    }
  },

  isWishlisted: (productSlug) => get().slugs.has(productSlug),

  // Optimistic: flips the heart instantly, reverts only if the request fails.
  toggle: async (productSlug) => {
    const wasWishlisted = get().slugs.has(productSlug);

    set((state) => {
      const slugs = new Set(state.slugs);
      if (wasWishlisted) slugs.delete(productSlug);
      else slugs.add(productSlug);
      return { slugs };
    });

    try {
      if (wasWishlisted) {
        await wishlistApi.remove(productSlug);
        set((state) => ({
          items: state.items.filter((i) => i.product_slug !== productSlug),
        }));
      } else {
        const { data } = await wishlistApi.add(productSlug);
        set((state) => ({ items: [data, ...state.items] }));
      }
    } catch {
      set((state) => {
        const slugs = new Set(state.slugs);
        if (wasWishlisted) slugs.add(productSlug);
        else slugs.delete(productSlug);
        return { slugs };
      });
    }
  },

  clear: () => set({ items: [], slugs: new Set() }),
}));
