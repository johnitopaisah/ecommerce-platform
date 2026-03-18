"use client";

import { X, CheckCircle } from "lucide-react";
import type { Order } from "@/types";
import { formatPrice, formatDate, getOrderStatusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useState } from "react";
import { ordersApi } from "@/lib/services";

const STATUS_TRANSITIONS: Record<string, string[]> = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["processing", "cancelled"],
  processing: ["shipped", "cancelled"],
  shipped: ["delivered"],
  delivered: ["refunded"],
  cancelled: [],
  refunded: [],
};

interface Props {
  order: Order;
  onClose: () => void;
  onStatusChange: (order: Order, newStatus: string) => Promise<void>;
  onRefresh: () => void;
}

export default function OrderDrawer({ order, onClose, onStatusChange, onRefresh }: Props) {
  const [updating, setUpdating] = useState(false);
  const [markingPaid, setMarkingPaid] = useState(false);
  const nextStatuses = STATUS_TRANSITIONS[order.status] || [];

  const handleUpdate = async (status: string) => {
    setUpdating(true);
    try { await onStatusChange(order, status); }
    finally { setUpdating(false); }
  };

  const handleMarkPaid = async () => {
    if (!confirm(`Mark order #${order.order_number} as paid?`)) return;
    setMarkingPaid(true);
    try {
      await ordersApi.markPaid(order.order_number);
      onRefresh();
      onClose();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Failed to mark as paid.");
    } finally {
      setMarkingPaid(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <p className="font-bold text-gray-900">#{order.order_number}</p>
            <p className="text-xs text-gray-400">{formatDate(order.created)}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">

          {/* Status + payment badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={getOrderStatusColor(order.status)}>
              {order.status_display}
            </Badge>
            {order.billing_status ? (
              <span className="text-xs text-green-700 bg-green-50 border border-green-200 px-2 py-1 rounded-full flex items-center gap-1">
                <CheckCircle size={11} /> Payment confirmed
              </span>
            ) : (
              <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2 py-1 rounded-full">
                Awaiting payment
              </span>
            )}
          </div>

          {/* Mark as paid (only if not already paid) */}
          {!order.billing_status && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm text-amber-800 mb-3">
                This order has not been confirmed as paid yet. If payment was received outside Stripe, mark it manually.
              </p>
              <Button
                size="sm"
                variant="primary"
                onClick={handleMarkPaid}
                isLoading={markingPaid}
                className="w-full"
              >
                <CheckCircle size={14} className="mr-1.5" />
                Mark as paid
              </Button>
            </div>
          )}

          {/* Customer */}
          <div className="bg-gray-50 rounded-xl p-4 space-y-1">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Customer</p>
            <p className="font-medium text-gray-900">{order.full_name}</p>
            <p className="text-sm text-gray-600">{order.email}</p>
            {order.phone && <p className="text-sm text-gray-600">{order.phone}</p>}
          </div>

          {/* Shipping */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Shipping address</p>
            <address className="not-italic text-sm text-gray-700 space-y-0.5">
              <p>{order.address_line_1}</p>
              {order.address_line_2 && <p>{order.address_line_2}</p>}
              <p>{order.city}{order.postcode ? `, ${order.postcode}` : ""}</p>
              <p>{order.country}</p>
            </address>
          </div>

          {/* Items */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Items</p>
            <div className="space-y-2">
              {order.items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm bg-gray-50 rounded-lg px-3 py-2">
                  <div>
                    <p className="font-medium text-gray-900">{item.product_title}</p>
                    <p className="text-xs text-gray-500">{item.quantity} × {formatPrice(item.price)}</p>
                  </div>
                  <p className="font-semibold text-gray-900">{formatPrice(item.line_total)}</p>
                </div>
              ))}
            </div>
            <div className="flex justify-between font-bold text-gray-900 mt-3 px-3">
              <span>Total</span>
              <span>{formatPrice(order.total_paid)}</span>
            </div>
          </div>
        </div>

        {/* Footer — status transitions */}
        {nextStatuses.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Update status</p>
            <div className="flex gap-2 flex-wrap">
              {nextStatuses.map((s) => (
                <Button
                  key={s}
                  size="sm"
                  variant={s === "cancelled" || s === "refunded" ? "danger" : "primary"}
                  onClick={() => handleUpdate(s)}
                  isLoading={updating}
                  className="capitalize"
                >
                  Mark as {s}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
