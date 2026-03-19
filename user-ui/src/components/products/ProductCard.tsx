"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { useState } from "react";
import type { Product } from "@/types";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { useBasketStore } from "@/store/basketStore";
import { Button } from "@/components/ui/Button";
import SafeImage from "@/components/ui/SafeImage";

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const { addItem, isLoading } = useBasketStore();
  const [added, setAdded] = useState(false);

  const handleAddToBasket = async (e: React.MouseEvent) => {
    e.preventDefault();
    await addItem(product.id, 1);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <Link href={`/products/${product.slug}`} className="group block">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
        {/* Image */}
        <div className="relative aspect-square bg-gray-50 overflow-hidden">
          <SafeImage
            src={getImageUrl(product.image)}
            alt={product.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
          />
          {!product.in_stock && (
            <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
              <span className="text-sm font-medium text-gray-500">Out of stock</span>
            </div>
          )}
          {product.discount_price && (
            <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
              Sale
            </span>
          )}
        </div>

        {/* Info */}
        <div className="p-4">
          <p className="text-xs text-gray-400 mb-1">{product.category_name}</p>
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-2 min-h-[2.5rem]">
            {product.title}
          </h3>

          {/* Price */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base font-bold text-gray-900">
              {formatPrice(product.effective_price)}
            </span>
            {product.discount_price && (
              <span className="text-sm text-gray-400 line-through">
                {formatPrice(product.price)}
              </span>
            )}
          </div>

          {/* Add to basket */}
          <Button
            variant={added ? "secondary" : "primary"}
            size="sm"
            className="w-full"
            onClick={handleAddToBasket}
            disabled={!product.in_stock || isLoading}
          >
            <ShoppingCart size={14} className="mr-1.5" />
            {added ? "Added!" : "Add to basket"}
          </Button>
        </div>
      </div>
    </Link>
  );
}
