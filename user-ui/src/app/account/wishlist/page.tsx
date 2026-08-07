"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Heart, ShoppingCart } from "lucide-react";
import { useWishlistStore } from "@/store/wishlistStore";
import { useBasketStore } from "@/store/basketStore";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import SafeImage from "@/components/ui/SafeImage";

export default function WishlistPage() {
  const { items, isLoading, fetchWishlist, toggle } = useWishlistStore();
  const { addItem } = useBasketStore();

  useEffect(() => { fetchWishlist(); }, [fetchWishlist]);

  if (isLoading && !items.length) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-xl h-24 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="text-center py-16">
        <Heart size={48} className="text-gray-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-700 mb-2">Your wishlist is empty</h2>
        <p className="text-sm text-gray-500 mb-6">
          Tap the heart on any product to save it for later.
        </p>
        <Link href="/products">
          <Button>Browse products</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">
        Wishlist
        <span className="ml-2 text-sm font-normal text-gray-400">({items.length})</span>
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex gap-4 bg-white border border-gray-200 rounded-xl p-4"
          >
            <Link href={`/products/${item.product_slug}`} className="relative w-20 h-20 shrink-0 rounded-lg overflow-hidden bg-gray-50">
              <SafeImage
                src={getImageUrl(item.product_image)}
                alt={item.product_title}
                fill
                className="object-cover"
                sizes="80px"
              />
            </Link>
            <div className="flex-1 min-w-0 flex flex-col">
              <p className="text-xs text-gray-400">{item.category_name}</p>
              <Link href={`/products/${item.product_slug}`} className="font-semibold text-gray-900 text-sm line-clamp-2 hover:underline">
                {item.product_title}
              </Link>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-bold text-gray-900 text-sm">{formatPrice(item.product_effective_price)}</span>
                {!item.product_in_stock && (
                  <span className="text-xs text-red-500">Out of stock</span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-auto pt-2">
                <Button
                  size="sm"
                  className="flex-1"
                  disabled={!item.product_in_stock}
                  onClick={() => addItem(item.product_id, 1)}
                >
                  <ShoppingCart size={13} className="mr-1.5" />
                  Add to basket
                </Button>
                <button
                  onClick={() => toggle(item.product_slug)}
                  aria-label="Remove from wishlist"
                  className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <Heart size={15} className="fill-red-500 text-red-500" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
