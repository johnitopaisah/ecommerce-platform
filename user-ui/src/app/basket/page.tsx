"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { useBasketStore } from "@/store/basketStore";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import SafeImage from "@/components/ui/SafeImage";

export default function BasketPage() {
  const { basket, updateItem, removeItem, isLoading } = useBasketStore();

  if (!basket.items.length) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">Your basket is empty</h1>
        <p className="text-gray-500 mb-8">Add some products to get started.</p>
        <Link href="/products">
          <Button size="lg">Continue shopping</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">
        Your basket ({basket.total_items}{" "}
        {basket.total_items === 1 ? "item" : "items"})
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Items */}
        <div className="flex-1 space-y-4">
          {basket.items.map((item) => (
            <div
              key={item.product_id}
              className="flex gap-4 bg-white border border-gray-200 rounded-xl p-4"
            >
              {/* Image */}
              <Link href={`/products/${item.slug}`} className="shrink-0">
                <div className="relative w-20 h-20 rounded-lg overflow-hidden bg-gray-100">
                  <SafeImage
                    src={getImageUrl(item.image)}
                    alt={item.title}
                    fill
                    className="object-cover"
                  />
                </div>
              </Link>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <Link href={`/products/${item.slug}`}>
                  <p className="font-semibold text-gray-900 text-sm hover:underline line-clamp-2">
                    {item.title}
                  </p>
                </Link>
                <p className="text-sm text-gray-500 mt-0.5">
                  {formatPrice(item.price)} each
                </p>

                {/* Qty controls */}
                <div className="flex items-center gap-3 mt-3">
                  <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                    <button
                      onClick={() => updateItem(item.product_id, item.qty - 1)}
                      disabled={isLoading}
                      className="px-2.5 py-1 text-gray-600 hover:bg-gray-100 text-sm"
                    >
                      −
                    </button>
                    <span className="px-3 py-1 text-sm font-medium">
                      {item.qty}
                    </span>
                    <button
                      onClick={() =>
                        updateItem(
                          item.product_id,
                          Math.min(item.stock_quantity, item.qty + 1)
                        )
                      }
                      disabled={isLoading || item.qty >= item.stock_quantity}
                      className="px-2.5 py-1 text-gray-600 hover:bg-gray-100 text-sm disabled:opacity-40"
                    >
                      +
                    </button>
                  </div>

                  <button
                    onClick={() => removeItem(item.product_id)}
                    disabled={isLoading}
                    className="text-red-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              {/* Line total */}
              <div className="shrink-0 text-right">
                <p className="font-bold text-gray-900">
                  {formatPrice(item.line_total)}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:w-72 shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl p-6 sticky top-24">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Order summary
            </h2>
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Subtotal</span>
                <span>{formatPrice(basket.subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
            </div>
            <div className="border-t border-gray-200 pt-4 mb-6">
              <div className="flex justify-between font-bold text-gray-900">
                <span>Total</span>
                <span>{formatPrice(basket.subtotal)}</span>
              </div>
            </div>
            <Link href="/checkout">
              <Button size="lg" className="w-full">
                Proceed to checkout
              </Button>
            </Link>
            <Link href="/products">
              <Button variant="ghost" size="sm" className="w-full mt-2">
                Continue shopping
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
