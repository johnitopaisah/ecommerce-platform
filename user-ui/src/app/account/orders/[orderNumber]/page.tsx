"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ordersApi } from "@/lib/services";
import type { Order } from "@/types";
import { formatPrice, getOrderStatusColor } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { ArrowLeft } from "lucide-react";

export default function OrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    ordersApi
      .detail(orderNumber)
      .then((res) => setOrder(res.data))
      .catch(() => router.replace("/account/orders"))
      .finally(() => setLoading(false));
  }, [orderNumber]);

  const handleCancel = async () => {
    if (!order || !confirm("Are you sure you want to cancel this order?")) return;
    setCancelling(true);
    try {
      const res = await ordersApi.cancel(order.order_number);
      setOrder(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Could not cancel order.");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return <div className="bg-gray-100 rounded-xl h-64 animate-pulse" />;
  }

  if (!order) return null;

  const canCancel = order.status === "pending" || order.status === "confirmed";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/account/orders" className="text-gray-400 hover:text-gray-700">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Order #{order.order_number}</h1>
      </div>

      {/* Status banner */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-sm text-gray-500">Placed on</p>
          <p className="font-semibold text-gray-900">
            {new Date(order.created).toLocaleDateString("en-GB", {
              day: "numeric", month: "long", year: "numeric",
            })}
          </p>
        </div>
        <span className={`text-sm px-3 py-1.5 rounded-full font-medium ${getOrderStatusColor(order.status)}`}>
          {order.status_display}
        </span>
        {canCancel && (
          <Button variant="danger" size="sm" onClick={handleCancel} isLoading={cancelling}>
            Cancel order
          </Button>
        )}
      </div>

      {/* Items */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Items</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {order.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between px-5 py-4">
              <div>
                <p className="font-medium text-sm text-gray-900">{item.product_title}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {item.quantity} × {formatPrice(item.price)}
                </p>
              </div>
              <p className="font-semibold text-sm text-gray-900">
                {formatPrice(item.line_total)}
              </p>
            </div>
          ))}
        </div>
        <div className="px-5 py-4 bg-gray-50 flex justify-between">
          <span className="font-semibold text-gray-900">Total</span>
          <span className="font-bold text-gray-900">{formatPrice(order.total_paid)}</span>
        </div>
      </div>

      {/* Shipping address */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="font-semibold text-gray-900 mb-3">Shipping address</h2>
        <address className="not-italic text-sm text-gray-600 space-y-1">
          <p className="font-medium text-gray-900">{order.full_name}</p>
          {order.phone && <p>{order.phone}</p>}
          <p>{order.address_line_1}</p>
          {order.address_line_2 && <p>{order.address_line_2}</p>}
          <p>{order.city}{order.postcode ? `, ${order.postcode}` : ""}</p>
          <p>{order.country}</p>
        </address>
      </div>
    </div>
  );
}
