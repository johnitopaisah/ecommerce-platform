"use client";

import { useState } from "react";
import { notFound } from "next/navigation";
import { ShoppingCart, Package } from "lucide-react";
import { productsApi } from "@/lib/services";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { useBasketStore } from "@/store/basketStore";
import { Button } from "@/components/ui/Button";
import SafeImage from "@/components/ui/SafeImage";
import type { Product } from "@/types";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let product: Product;
  try {
    const res = await productsApi.detail(slug);
    product = res.data;
  } catch {
    notFound();
  }

  return <ProductDetailClient product={product} />;
}

function ProductDetailClient({ product }: { product: Product }) {
  const { addItem, isLoading } = useBasketStore();
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);

  const handleAdd = async () => {
    await addItem(product.id, qty);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {/* Image */}
        <div className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden">
          <SafeImage
            src={getImageUrl(product.image)}
            alt={product.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 50vw"
            priority
          />
          {product.discount_price && (
            <span className="absolute top-4 left-4 bg-red-500 text-white text-sm font-semibold px-3 py-1 rounded-full">
              Sale
            </span>
          )}
        </div>

        {/* Info */}
        <div className="flex flex-col">
          {product.category && (
            <p className="text-sm text-gray-500 mb-2">{product.category.name}</p>
          )}
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
            {product.title}
          </h1>

          {/* Price */}
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl font-bold text-gray-900">
              {formatPrice(product.effective_price)}
            </span>
            {product.discount_price && (
              <span className="text-lg text-gray-400 line-through">
                {formatPrice(product.price)}
              </span>
            )}
          </div>

          {/* Stock */}
          <div className="flex items-center gap-2 mb-6">
            <Package
              size={16}
              className={product.in_stock ? "text-green-500" : "text-red-400"}
            />
            <span
              className={`text-sm font-medium ${
                product.in_stock ? "text-green-600" : "text-red-500"
              }`}
            >
              {product.in_stock
                ? `${product.stock_quantity} in stock`
                : "Out of stock"}
            </span>
          </div>

          {/* Description */}
          {product.description && (
            <p className="text-gray-600 text-sm leading-relaxed mb-8">
              {product.description}
            </p>
          )}

          {/* Quantity + Add */}
          {product.in_stock && (
            <div className="flex items-center gap-3 mt-auto">
              <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                <button
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="px-3 py-2 text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  −
                </button>
                <span className="px-4 py-2 text-sm font-medium text-gray-900 min-w-[2.5rem] text-center">
                  {qty}
                </span>
                <button
                  onClick={() =>
                    setQty((q) => Math.min(product.stock_quantity, q + 1))
                  }
                  className="px-3 py-2 text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  +
                </button>
              </div>

              <Button
                size="lg"
                className="flex-1"
                onClick={handleAdd}
                isLoading={isLoading}
                variant={added ? "secondary" : "primary"}
              >
                <ShoppingCart size={18} className="mr-2" />
                {added ? "Added to basket!" : "Add to basket"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
