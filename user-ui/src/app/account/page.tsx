"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { useEffect, useState } from "react";
import { ordersApi } from "@/lib/services";
import type { Order } from "@/types";
import { formatPrice, getOrderStatusColor } from "@/lib/utils";
import { ShoppingBag, User, Package } from "lucide-react";

export default function AccountDashboard() {
  const { user } = useAuthStore();
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);

  useEffect(() => {
    ordersApi.list().then((res) => setRecentOrders(res.data.slice(0, 3))).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Welcome card */}
      <div className="bg-gray-900 text-white rounded-xl p-6">
        <p className="text-gray-400 text-sm mb-1">Welcome back,</p>
        <p className="text-xl font-bold">{user?.full_name || user?.user_name}</p>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          href="/account/orders"
          className="bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-900 transition-colors flex items-center gap-4"
        >
          <div className="bg-gray-100 rounded-lg p-3">
            <ShoppingBag size={20} className="text-gray-700" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">Orders</p>
            <p className="text-xs text-gray-500">View order history</p>
          </div>
        </Link>
        <Link
          href="/account/profile"
          className="bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-900 transition-colors flex items-center gap-4"
        >
          <div className="bg-gray-100 rounded-lg p-3">
            <User size={20} className="text-gray-700" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">Profile</p>
            <p className="text-xs text-gray-500">Edit your details</p>
          </div>
        </Link>
        <Link
          href="/products"
          className="bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-900 transition-colors flex items-center gap-4"
        >
          <div className="bg-gray-100 rounded-lg p-3">
            <Package size={20} className="text-gray-700" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">Shop</p>
            <p className="text-xs text-gray-500">Browse products</p>
          </div>
        </Link>
      </div>

      {/* Recent orders */}
      {recentOrders.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-900">Recent orders</h2>
            <Link href="/account/orders" className="text-sm text-gray-500 hover:underline">
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {recentOrders.map((order) => (
              <Link
                key={order.id}
                href={`/account/orders/${order.order_number}`}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-gray-400 transition-colors"
              >
                <div>
                  <p className="font-medium text-sm text-gray-900">#{order.order_number}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(order.created).toLocaleDateString("en-GB", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${getOrderStatusColor(order.status)}`}>
                    {order.status_display}
                  </span>
                  <span className="font-semibold text-sm text-gray-900">
                    {formatPrice(order.total_paid)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
