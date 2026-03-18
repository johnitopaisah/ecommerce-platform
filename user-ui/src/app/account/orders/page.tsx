"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ordersApi } from "@/lib/services";
import type { Order } from "@/types";
import { formatPrice, getOrderStatusColor } from "@/lib/utils";
import { PackageOpen } from "lucide-react";
import { Button } from "@/components/ui/Button";
import type { AxiosResponse } from "axios";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ordersApi
      .list()
      .then((res: AxiosResponse<Order[]>) => setOrders(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-xl h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!orders.length) {
    return (
      <div className="text-center py-16">
        <PackageOpen size={48} className="text-gray-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-700 mb-2">No orders yet</h2>
        <p className="text-sm text-gray-500 mb-6">
          Your orders will appear here once you place them.
        </p>
        <Link href="/products">
          <Button>Start shopping</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">
        Orders
        <span className="ml-2 text-sm font-normal text-gray-400">({orders.length})</span>
      </h1>
      {orders.map((order) => (
        <Link
          key={order.id}
          href={`/account/orders/${order.order_number}`}
          className="block bg-white border border-gray-200 rounded-xl px-5 py-4 hover:border-gray-400 transition-colors"
        >
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="font-semibold text-gray-900">#{order.order_number}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {new Date(order.created).toLocaleDateString("en-GB", {
                  day: "numeric", month: "long", year: "numeric",
                })}
                {" · "}
                {order.items.length} {order.items.length === 1 ? "item" : "items"}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${getOrderStatusColor(order.status)}`}>
                {order.status_display}
              </span>
              {!order.billing_status && (
                <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2 py-1 rounded-full">
                  Awaiting payment
                </span>
              )}
              <span className="font-bold text-gray-900">{formatPrice(order.total_paid)}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
