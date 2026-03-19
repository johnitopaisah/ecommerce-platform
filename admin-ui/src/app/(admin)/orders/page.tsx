"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, ChevronRight } from "lucide-react";
import { ordersApi } from "@/lib/services";
import type { Order } from "@/types";
import { formatPrice, formatDate, getOrderStatusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import OrderDrawer from "./OrderDrawer";

const STATUS_OPTIONS = [
  { label: "All", value: "" },
  { label: "Pending", value: "pending" },
  { label: "Confirmed", value: "confirmed" },
  { label: "Processing", value: "processing" },
  { label: "Shipped", value: "shipped" },
  { label: "Delivered", value: "delivered" },
  { label: "Cancelled", value: "cancelled" },
];

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Order | null>(null);

  const fetchOrders = useCallback(async (status: string) => {
    setLoading(true);
    try {
      const res = await ordersApi.list(status ? { status } : undefined);
      setOrders(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchOrders(statusFilter);
  }, [statusFilter, fetchOrders]);

  const handleStatusChange = async (order: Order, newStatus: string) => {
    await ordersApi.updateStatus(order.order_number, newStatus);
    void fetchOrders(statusFilter);
    setSelected(null);
  };

  const filtered = orders.filter(
    (o) =>
      o.order_number.toLowerCase().includes(search.toLowerCase()) ||
      o.full_name.toLowerCase().includes(search.toLowerCase()) ||
      o.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <p className="text-sm text-gray-500 mt-0.5">{orders.length} orders</p>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex bg-gray-100 rounded-lg p-1 gap-1 flex-wrap">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                statusFilter === opt.value
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search order, name, email…"
            className="pl-8 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 w-64"
          />
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading orders…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {["Order", "Customer", "Status", "Paid", "Total", "Date", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((order) => (
                  <tr
                    key={order.id}
                    className="hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => setSelected(order)}
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">#{order.order_number}</p>
                      <p className="text-xs text-gray-400">{order.items.length} item{order.items.length !== 1 ? "s" : ""}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{order.full_name}</p>
                      <p className="text-xs text-gray-400">{order.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={getOrderStatusColor(order.status)}>{order.status_display}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {order.billing_status ? (
                        <span className="text-xs text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">Yes</span>
                      ) : (
                        <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">Pending</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{formatPrice(order.total_paid)}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(order.created)}</td>
                    <td className="px-4 py-3"><ChevronRight size={15} className="text-gray-300" /></td>
                  </tr>
                ))}
                {!filtered.length && (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-sm text-gray-400">No orders found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selected && (
        <OrderDrawer
          order={selected}
          onClose={() => setSelected(null)}
          onStatusChange={handleStatusChange}
          onRefresh={() => { void fetchOrders(statusFilter); setSelected(null); }}
        />
      )}
    </div>
  );
}
